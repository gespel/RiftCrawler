#[macro_use] extern crate rocket;
use rocket::fs::{FileServer, relative};
use rocket::response::content::{RawHtml, RawJson};
use rocket::serde::{json::Json};
use std::fs;

mod gameslist;
use crate::gameslist::GamesList;

#[get("/")]
async fn index() -> RawHtml<String> {
    // HTML aus Datei laden
    let html = fs::read_to_string(relative!("static/index.html"))
        .unwrap_or_else(|_| String::from("<h1>Error loading index.html</h1>"));
    
    RawHtml(html)
}

#[get("/<id>")]
async fn get_game(id: &str) -> RawJson<String> {
    let path = [relative!("../crawler/games/classic/"), id].concat();
    match fs::read_to_string(&path) {
        Ok(f) => {
            RawJson(
                f
            )
        }
        Err(_) => {
            println!("{}", path);
            RawJson("{\"status\": \"404\"}".to_string())
        }
    }
}

#[get("/")]
async fn get_all_games() -> Json<GamesList> {
    Json(GamesList::new(relative!("../crawler/games/classic").to_string()))
}

#[rocket::main]
async fn main() -> Result<(), rocket::Error> {
    rocket::build()
        .mount("/", routes![index])
        .mount("/game", routes![get_game])
        .mount("/all-games", routes![get_all_games])
        .mount("/static", FileServer::from(relative!("static")))
        .launch()
        .await?;
    
    Ok(())
}
