use rocket::serde::{Serialize};
use crate::analysis::models::participant::Participant;
use crate::analysis::models::team::Team;

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub struct Game {
    pub info: GameInfo,
    pub metadata: GameMetadata
}

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
struct GameInfo {
    pub game_creation: u64,
    pub game_duration: u32,
    pub game_end_timestamp: u128,
    pub game_id: String,
    pub game_mode: String,
    pub game_name: String,
    pub game_start_timestamp: u128,
    pub game_type: String,
    pub game_version: String,
    pub map_id: u8,
    pub participants: Vec<Participant>,
    pub platform_id: String,
    pub queue_id: u8,
    pub teams: Vec<Team>,
    pub tournament_code: String
}

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
struct GameMetadata {
    pub data_version: String,
    pub match_id: String,
    pub participants: Vec<String>
}