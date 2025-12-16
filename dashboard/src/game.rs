use rocket::serde::{Serialize, json::Json};


#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub struct Game {
    pub id: String
}