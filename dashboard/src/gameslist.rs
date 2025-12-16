use rocket::serde::{Serialize};
use std::fs;

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub struct GamesList {
    pub games: Vec<String>,
    pub num_of_games: u16
}

impl GamesList {
    pub fn new(folder: String) -> GamesList {
        let paths = fs::read_dir(folder.as_str()).unwrap();
        let mut games_paths: Vec<String> = vec![];

        for path in paths {
            let name = path.unwrap().file_name().into_string().unwrap();
            games_paths.push(name);
        }
        GamesList {
            games: games_paths.clone(),
            num_of_games: games_paths.len() as u16
        }
    }
}
