use std::fs;
use std::fs::File;
use std::io::Write;
use serde_json::{Error, Value};
use serde_json::Value::String;
use log::info;
use crate::lsgcclient::LSGCClient;
mod lsgcclient;

#[tokio::main]
async fn main() -> Result<(), Error> {
    env_logger::init();
    let mut l = LSGCClient::new("RGAPI-da023584-df15-4d8b-b0b8-f2b5630bbd6f".parse().unwrap());
    println!("Starting initial Playerfetch");
    let a = l.request("https://euw1.api.riotgames.com/lol/spectator/v4/featured-games".to_string())
        .await
        .expect("error while requesting");
    let parsed: Value = serde_json::from_str(&*a)?;
    let mut m_players: Vec<std::string::String> = Vec::new();
    if let Some(games) = parsed["gameList"].as_array() {
        for game in games {
            if let Some(players) = game["participants"].as_array() {
                for player in players {
                    m_players.push(player["puuid"].clone().to_string());
                }
            }
        }
    }
    println!("Starting initial Gamefetch");
    let mut games_list: Vec<std::string::String> = Vec::new();
    for player in m_players.iter() {
        let uri = format!("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?start=0&count=5", player.to_string().trim_matches('\"'));
        let a = l.request(uri.parse().unwrap())
            .await
            .expect("error while requesting");
        let parsed: Value = serde_json::from_str(&*a)?;
        if let Some(games) = parsed.as_array() {
            for game in games {
                games_list.push(game.to_string());
            }
        }
    }

    let mut new_player_list = Vec::new();
    loop {
        println!("New Epoch!");
        println!("Fetching Games..");
        for game in games_list.iter() {
            //game_json_list.push(parsed.clone());
            if fs::metadata(game.to_string().trim_matches('\"').to_owned() + ".json").is_err() {
                let uri = format!("https://europe.api.riotgames.com/lol/match/v5/matches/{}", game.to_string().trim_matches('\"'));
                println!("Requesting {}", uri);
                let a = l.request(uri.parse().unwrap())
                    .await
                    .expect("Error");
                let parsed: Value = serde_json::from_str(&*a)?;
                let mut file = File::create(parsed["metadata"]["matchId"].to_string().trim_matches('\"').to_owned() + ".json").expect("Error while filewrite!");
                let fjson = serde_json::to_string_pretty(&parsed).expect("Fehler beim Formatieren des JSON");
                file.write_all(fjson.as_bytes()).expect("Error while writing json to file!");
            }
            else {
                println!("Game already exists!");
            }
            if let Some(players) = parsed["metadata"]["participants"].as_array() {
                for player in players {
                    new_player_list.push(player["puuid"].clone().to_string());
                }
            }
        }

        games_list.clear();


        println!("Fetching Players...");
        for player in new_player_list.iter() {
            let uri = format!("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?start=0&count=100", player.to_string().trim_matches('\"'));
            println!("Requesting {} now", player.to_string());
            let a = l.request(uri.parse().unwrap())
                .await
                .expect("error while requesting");
            let parsed: Value = serde_json::from_str(&*a)?;
            if let Some(games) = parsed.as_array() {
                for game in games {
                    games_list.push(game.to_string());
                }
            }
        }
    }



    Ok(())
}

