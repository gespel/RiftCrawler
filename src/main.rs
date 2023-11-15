
use std::io::Write;
use serde_json::{Error, Value};
use log::{error, info};
use crate::lsgcclient::LSGCClient;
mod lsgcclient;


#[tokio::main]
async fn main() -> Result<(), Error> {
    env_logger::init();
    let mut l = LSGCClient::new("RGAPI-414e3e19-3cb5-402f-a7ff-56bea7e62375".parse().unwrap());
    info!("Starting initial Playerfetch");

    l.get_featured_games_players().await.expect("TODO: panic message");

    info!("Starting initial Gamefetch");


    l.get_games_from_players(2).await.expect("TODO: panic message");

    loop {
        info!("New Epoch!");
        info!("Writing to disk and extracting new players..");
        l.write_games_to_disk_and_extract_new_players().await.expect("TODO: panic message");

        info!("Fetching games from players...");
        l.get_games_from_players(2).await.expect("TODO: panic message");
    }



    Ok(())
}

