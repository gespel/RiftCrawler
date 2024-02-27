use std::fs;
use std::fs::File;
use std::io::Write;
use tokio::time::{sleep, Duration};
use reqwest::header::HeaderMap;
use indicatif::{ProgressBar, ProgressStyle};
use log::{debug, info, warn};
use reqwest::Client;
use serde_json::Value;
use rand::Rng;
use crate::tools;

pub struct RiftCrawler {
    pulls_this_second: i32,
    pulls_last_two_minutes: i32,
    client: reqwest::Client,
    header: HeaderMap,
    pub games_list: Vec<std::string::String>,
    pub player_list: Vec<std::string::String>
}

impl RiftCrawler {
    async fn sleep_with_status(&self) {
        let progress = ProgressBar::new(120);
        progress.set_style(
            ProgressStyle::default_bar()
                .template("[{wide_bar}] {percent}%").unwrap()
                .progress_chars("=> "),
        );
        for i in 0..120 {
            sleep(Duration::from_secs(1)).await; // Simuliere eine Verzögerung
            progress.inc(1);
        }
        progress.finish();
    }
    pub fn new(api_key: String) -> RiftCrawler {
        let mut hm = HeaderMap::new();
        hm.insert("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36".parse().unwrap());
        hm.insert("Accept-Language", "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7".parse().unwrap());
        hm.insert("Accept-Charset", "application/x-www-form-urlencoded; charset=UTF-8".parse().unwrap());
        hm.insert("Origin", "http://sten-heimbrodt.de/lolstats".parse().unwrap());
        hm.insert("X-Riot-Token", api_key.parse().unwrap());

        let out = RiftCrawler {
            pulls_this_second: 0,
            pulls_last_two_minutes: 0,
            client: reqwest::Client::new(),
            header: hm,
            games_list: vec![],
            player_list: vec![],
        };
        return out;
    }
    pub async fn request(&mut self, uri: String) -> Result<String, reqwest::Error> {
        self.pulls_this_second += 1;
        self.pulls_last_two_minutes += 1;

        if self.pulls_this_second >= 20 {
            sleep(Duration::from_secs(1)).await;
            self.pulls_this_second = 0;
        }

        if self.pulls_last_two_minutes >= 100 {
            self.sleep_with_status().await;
            self.pulls_last_two_minutes = 0;
        }

        let h = &self.header;
        let response = self.client
            .get(uri)
            .headers(h.clone())
            .send()
            .await?;

        if response.status().is_success() {
            //println!("{} Request was successful", self.pulls_last_two_minutes);
            //println!("{}", response.text().clone());
        } else {
            println!("Request failed with status code: {}", response.status());
            if response.status() == 429 {
                self.sleep_with_status().await;
            }
        }

        Ok(response.text().await?)
    }

    pub async fn get_featured_games_players(&mut self) -> Result<(), reqwest::Error> {
        let a = self.request("https://euw1.api.riotgames.com/lol/spectator/v4/featured-games".to_string())
            .await
            .expect("error while requesting");
        let parsed: Value = serde_json::from_str(&*a).unwrap();
        println!("{}", a);
        if let Some(games) = parsed["gameList"].as_array() {
            for game in games {
                if let Some(players) = game["participants"].as_array() {
                    for player in players {
                        self.player_list.push(player["puuid"].to_string().trim_matches('\"').parse().unwrap());
                    }
                }
            }
        }
        Ok(())
    }

    pub async fn get_games_from_player(&mut self, player: &str) -> Result<(), reqwest::Error> {
        let a = self.request(format!("https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{player}").to_string()).await.expect("");
        let player_json: Value = serde_json::from_str(a.as_str()).unwrap();
        let mut puuid: String = player_json["puuid"].as_str().unwrap().to_string();
        let a2 = self.request(format!("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids").to_string()).await.expect("");
        let games_json: Vec<String> = serde_json::from_str(&*a2).unwrap();

        for game in games_json {
            self.games_list.push(game);
        }

        Ok(())
    }

    pub async fn get_games_from_players(&mut self, player_number: usize) -> Result<(), reqwest::Error> {
        let mut player_selection: Vec<String> = Vec::new();
        let mut rng = rand::thread_rng();
        for i in 0..player_number {
            let rand_num: usize = rng.gen_range(0..self.player_list.len());
            let p = self.player_list[rand_num].clone();
            player_selection.push(p);
        }
        self.player_list.clear();
        let uris: Vec<String> = player_selection.iter()
            .map(|player| {
                let name = player.trim_matches('\"');
                format!("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?start=1&count=1", name)
            })
            .collect();

        for uri in uris {
            let answer_json = self.request(uri.parse().unwrap())
                .await
                .expect("error while requesting");
            let parsed: Value = serde_json::from_str(&*answer_json).unwrap();
            if let Some(games) = parsed.as_array() {
                for game in games {
                    self.games_list.push(game.as_str().unwrap().to_string());
                }

            }
        }

        Ok(())
    }

    pub async fn write_games_to_disk_and_extract_new_players(&mut self) -> Result<(), reqwest::Error> {
        for game in self.games_list.clone() {
            if fs::metadata(game.to_string().trim_matches('\"').to_owned() + ".json").is_err() {
                let uri = format!("https://europe.api.riotgames.com/lol/match/v5/matches/{}", game.to_string().trim_matches('\"'));
                debug!("Requesting {}", uri);
                let a = self.request(uri.parse().unwrap())
                    .await
                    .expect("Error");
                let parsed: Value = serde_json::from_str(&*a).unwrap();

                let mut add_counter: usize = 0;

                if let Some(players) = parsed["metadata"]["participants"].as_array() {
                    for player in players {
                        debug!("New Player added! {}", player);
                        self.player_list.push(player.as_str().unwrap().to_string());
                        add_counter += 1;
                    }
                }
                info!("Added {} new players...", add_counter);
                if parsed["info"]["gameMode"] == "CLASSIC" {
                    tools::write_game_json_to_disk(parsed, tools::GameType::CLASSIC);
                }
                else if parsed["info"]["gameMode"] == "ARAM" {
                    tools::write_game_json_to_disk(parsed, tools::GameType::ARAM);
                }
                else {
                    debug!("Game is not classic...")
                }
            } else {
                debug!("Game already exists!");
            }

        }
        self.games_list.clear();
        self.player_list.sort();
        self.player_list.dedup();
        Ok(())
    }
}
