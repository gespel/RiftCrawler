
use std::io::Write;
use serde_json::{Error, Value};
use log::{error, info};
use crate::lsgcclient::LSGCClient;
mod lsgcclient;
mod tools;


#[tokio::main]
async fn main() -> Result<(), Error> {
    env_logger::init();

    info!("Setting up file structure now...");
    tools::setup_folder("games".to_string());
    tools::setup_folder("games/classic".to_string());
    tools::setup_folder("games/aram".to_string());
    info!("File structure done!");

    let mut l = LSGCClient::new("RGAPI-161bcb0a-9b72-4ad9-b04c-cc20b43df527".parse().unwrap());
    info!("Starting initial Playerfetch");
    l.get_featured_games_players().await.expect("TODO: panic message");

    loop {
        info!("New Epoch!");

        info!("Fetching games from players...");
        l.get_games_from_players(5).await.expect("TODO: panic message");

        info!("Writing to disk and extracting new players..");
        l.write_games_to_disk_and_extract_new_players().await.expect("TODO: panic message");

    }



    Ok(())
}

