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
    
    // Test-Kontext einfügen (könnte später durch ein Template-System ersetzt werden)
    let context_html = html.replace(
        "Dies ist ein einfaches Tailwind CSS Beispiel mit schönen Styling-Komponenten.",
        "Dashboard läuft! Server-Zeit: 16. Dezember 2025 | Status: ✅ Aktiv | Crawler: 🔍 Bereit"
    );
    
    RawHtml(context_html)
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
