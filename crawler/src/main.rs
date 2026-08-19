#![allow(dead_code)]
#![allow(unused_imports)]
use serde_json::{Error};
use log::{error, info};
use std::env;
use clap::{Parser, builder::Str};
use crate::riftcrawler::RiftCrawler;
mod riftcrawler;
mod tools;




#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Cli {
    ///API key can be retrieved from Riots Developer Portal
    #[arg(short, long)]
    api_key: Option<String>,

    ///The first account to start the crawl on
    #[arg(short, long)]
    start_account: Option<String>,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    env::set_var("RUST_LOG", "debug");
    env_logger::init();

    let mut api_key: String = String::new();

    if env::var("RIOT_API_KEY").is_ok() {
        api_key = env::var("RIOT_API_KEY").unwrap();
        info!("RIOT_API_KEY found in environment variables.");
        dbg!("API key: {}", &api_key);
    }

    let args = Cli::parse();

    if let Some(key) = &args.api_key {
        api_key = key.clone();
        info!("RIOT_API_KEY found in command line arguments.");
        dbg!("API key: {}", &api_key);
    }

    if api_key.is_empty() {
        error!("No API key provided. Please set the RIOT_API_KEY environment variable or provide it as a command line argument.");
        std::process::exit(1);
    }

    info!("Setting up file structure now...");
    tools::setup_folder("games".to_string());
    tools::setup_folder("games/classic".to_string());
    tools::setup_folder("games/aram".to_string());
    info!("File structure done!");

    let mut rc = RiftCrawler::new(api_key);
    let name: String;
    let tag_line: String;
    if let Some(start_account) = &args.start_account {
        let splitted = start_account.split(":").collect::<Vec<&str>>();
        if splitted.len() != 2 {
            error!("Invalid start account format. Please use the format 'name:tag_line'.");
            std::process::exit(1);
        }
        name = splitted[0].to_string();
        tag_line = splitted[1].to_string();

        info!("Starting crawl with account: {}", &name);
    } else {
        name = "TFO Gespel".to_string();
        tag_line = "EUW".to_string();
        info!("No starting account provided. Using default account: {}", &name);
    }

    /*let puuid = rc.get_player_puuid(name, tag_line).await;
    info!("Player puuid: {}", puuid);
    let level = rc.get_player_level(puuid.as_str()).await;
    info!("{} #{} is level {}", name, tag_line, level);*/
    loop {
        match rc.get_games_from_player(&name, &tag_line).await {
            Ok(_) => {}
            Err(_) => {error!("Failed to get games for player {}!", name);}
        }
        match rc.write_games_to_disk_and_extract_new_players().await {
            Ok(_) => {}
            Err(_) => {error!("Failed to write games to disk!");}
        }
        loop {
            match rc.get_games_from_players(5).await {
                Ok(_) => {}
                Err(_) => {error!("Failed to get games from players!");}
            }
            match rc.write_games_to_disk_and_extract_new_players().await {
                Ok(_) => {}
                Err(_) => {error!("Failed to write games to disk!");}
            }
        }
    }
}

