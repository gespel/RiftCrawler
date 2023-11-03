use std::fs;
use std::fs::File;
use std::io::Write;
use tokio::time::{sleep, Duration};
use reqwest::header::HeaderMap;
use indicatif::{ProgressBar, ProgressStyle};
use log::{debug, info, warn};
use reqwest::Client;
use serde_json::Value;

pub struct LSGCClient {
    pulls_this_second: i32,
    pulls_last_two_minutes: i32,
    client: reqwest::Client,
    header: HeaderMap,
    games_list: Vec<std::string::String>,
    player_list: Vec<std::string::String>
}

impl LSGCClient {
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
    pub fn new(api_key: String) -> LSGCClient {
        let mut hm = HeaderMap::new();
        hm.insert("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36".parse().unwrap());
        hm.insert("Accept-Language", "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7".parse().unwrap());
        hm.insert("Accept-Charset", "application/x-www-form-urlencoded; charset=UTF-8".parse().unwrap());
        hm.insert("Origin", "http://sten-heimbrodt.de/lolstats".parse().unwrap());
        hm.insert("X-Riot-Token", api_key.parse().unwrap());

        let out = LSGCClient {
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

    pub async fn get_games_from_players(&mut self) -> Result<(), reqwest::Error> {
        let uris: Vec<String> = self.player_list.iter()
            .map(|player| {
                let name = player.to_string().trim_matches('\"').to_string();
                format!("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?start=1&count=1", name)
            })
            .collect();

        // Now that you've collected the necessary data, you can make the requests
        for uri in uris {
            let a = self.request(uri.parse().unwrap())
                .await
                .expect("error while requesting");
            let parsed: Value = serde_json::from_str(&*a).unwrap();
            if let Some(games) = parsed.as_array() {
                for game in games {
                    self.games_list.push(game.to_string());
                }

            }
        }

        Ok(())
    }

    pub async fn write_games_to_disk_and_extract_new_players(&mut self) -> Result<(), reqwest::Error> {
        let games_list_temp: Vec<String> = self.games_list.clone();
        /*
        let games_list_temp: Vec<String> = self.games_list.iter()
            .map(|game| {
                let id = game.to_string().trim_matches('\"').to_string();
                format!("{}", id)
            })
            .collect();*/

        for game in games_list_temp {
            if fs::metadata(game.to_string().trim_matches('\"').to_owned() + ".json").is_err() {
                let uri = format!("https://europe.api.riotgames.com/lol/match/v5/matches/{}", game.to_string().trim_matches('\"'));
                debug!("Requesting {}", uri);
                let a = self.request(uri.parse().unwrap())
                    .await
                    .expect("Error");
                let parsed: Value = serde_json::from_str(&*a).unwrap();
                if parsed["info"]["gameMode"] == "CLASSIC" {
                    let mut file = File::create(parsed["metadata"]["matchId"].to_string().trim_matches('\"').to_owned() + ".json").expect("Error while filewrite!");
                    let fjson = serde_json::to_string_pretty(&parsed).expect("Fehler beim Formatieren des JSON");
                    file.write_all(fjson.as_bytes()).expect("Error while writing json to file!");
                    info!("{} Game written!", parsed["metadata"]["matchId"]);
                    if let Some(players) = parsed["metadata"]["participants"].as_array() {
                        for player in players {
                            self.player_list.push(player["puuid"].clone().to_string());
                        }
                    }
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
