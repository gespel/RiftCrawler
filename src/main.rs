
use std::io::Write;
use serde_json::{Error, Value};
use log::{error, info};
use crate::riftcrawler::RiftCrawler;
mod riftcrawler;
mod tools;


#[tokio::main]
async fn main() -> Result<(), Error> {
    env_logger::init();

    info!("Setting up file structure now...");
    tools::setup_folder("games".to_string());
    tools::setup_folder("games/classic".to_string());
    tools::setup_folder("games/aram".to_string());
    info!("File structure done!");

    let mut l = RiftCrawler::new("RGAPI-186290bf-d19d-4d83-b9e5-63ba02f738ff".parse().unwrap());
    info!("Starting initial Playerfetch");
    l.get_games_from_player("TFO Gespel").await.expect("TODO: panic message");
    l.write_games_to_disk_and_extract_new_players().await.expect("");
    loop {
        info!("New Epoch!");

        info!("Fetching games from players...");
        l.get_games_from_players(5).await.expect("TODO: panic message");

        info!("Writing to disk and extracting new players..");
        l.write_games_to_disk_and_extract_new_players().await.expect("TODO: panic message");

    }


    Ok(())
}

