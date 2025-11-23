#![allow(dead_code)]
#![allow(unused_imports)]
use serde_json::{Error};
use log::{info};
use std::env;
use clap::Parser;
use crate::riftcrawler::RiftCrawler;
mod riftcrawler;
mod tools;




#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Cli {
    ///API key can be retrieved from Riots Developer Portal
    #[arg(short, long)]
    api_key: String,

    ///The first account to start the crawl on
    #[arg(short, long)]
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

    let mut rc = RiftCrawler::new(args.api_key.parse().unwrap());
    let name = "TFO Gespel";
    let tag_line = "EUW";
    let puuid = rc.get_player_puuid(name, tag_line).await;
    info!("Player puuid: {}", puuid);
    let level = rc.get_player_level(puuid.as_str()).await;
    info!("{} #{} is level {}", name, tag_line, level);

    Ok(())
}

