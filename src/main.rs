#![allow(dead_code)]
#![allow(unused_imports)]
use serde_json::{Error};
use log::{info};
use std::env;
use clap::Parser;
use crate::riftcrawler::RiftCrawler;
mod riftcrawler;
mod tools;




#[derive(Parser)]
struct Cli {
    api_key: String,
    start_account: String,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    env::set_var("RUST_LOG", "debug");
    env_logger::init();
    let args = Cli::parse();


    info!("Setting up file structure now...");
    tools::setup_folder("games".to_string());
    tools::setup_folder("games/classic".to_string());
    tools::setup_folder("games/aram".to_string());
    info!("File structure done!");

    let mut l = RiftCrawler::new(args.api_key.parse().unwrap());
    info!("Starting initial Playerfetch");
    l.get_games_from_player(args.start_account.to_string()).await.expect("TODO: panic message");
    l.write_games_to_disk_and_extract_new_players().await.expect("");
    loop {
        info!("New Epoch!");

        info!("Fetching games from players...");
        l.get_games_from_players(5).await.expect("TODO: panic message");

        info!("Writing to disk and extracting new players..");
        l.write_games_to_disk_and_extract_new_players().await.expect("TODO: panic message");

    }
}

