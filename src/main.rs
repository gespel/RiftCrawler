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
    let mut l = LSGCClient::new("RGAPI-b99cf43d-d54a-440d-ae3d-b2d911d2c32c".parse().unwrap());
    println!("Starting initial Playerfetch");

    l.get_featured_games_players().await.expect("TODO: panic message");

    println!("Starting initial Gamefetch");


    l.get_games_from_players().await.expect("TODO: panic message");

    loop {
        println!("New Epoch!");
        println!("Fetching Games..");
        l.write_games_to_disk_and_extract_new_players().await.expect("TODO: panic message");

        println!("Fetching Players...");
        l.get_games_from_players().await.expect("TODO: panic message");
    }



    Ok(())
}

