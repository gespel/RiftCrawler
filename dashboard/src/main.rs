#[macro_use] extern crate rocket;
use rocket::fs::{FileServer, relative};
use rocket::response::content::RawHtml;
use rocket::serde::{Serialize, json::Json};
use std::fs;

mod game;
use crate::game::Game;


#[get("/")]
async fn index() -> RawHtml<String> {
    // HTML aus Datei laden
    let html = fs::read_to_string(relative!("static/index.html"))
        .unwrap_or_else(|_| String::from("<h1>Error loading index.html</h1>"));
    
    RawHtml(html)
}

#[get("/<id>")]
async fn get_game(id: &str) -> Json<Game> {
    Json(Game{id: id.to_string()})
}

#[rocket::main]
async fn main() -> Result<(), rocket::Error> {
    rocket::build()
        .mount("/", routes![index])
        .mount("/game", routes![get_game])
        .mount("/static", FileServer::from(relative!("static")))
        .launch()
        .await?;
    
    Ok(())
}
