use serde_json::{Error, Value};
use serde_json::Value::String;
use crate::lsgcclient::LSGCClient;
mod lsgcclient;

#[tokio::main]
async fn main() -> Result<(), Error> {
    let mut l = LSGCClient::new("RGAPI-3997e725-ff9a-4b69-8d12-58913508fdd0".parse().unwrap());
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

    loop {
        let mut games_list: Vec<std::string::String> = Vec::new();
        for player in m_players.iter() {
            let uri = format!("https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?start=0&count=20", player.to_string().trim_matches('\"'));
            println!("Requesting {} now", uri);
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


        let new_player_list = Vec::new();
        for game in games_list.iter() {

        }

        games_list.sort();
        games_list.dedup();

        for game in games_list.iter() {
            println!("{}", game);
        }
    }



    Ok(())
}

