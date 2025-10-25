use std::fs;
use std::fs::File;
use std::io::Write;
use std::path::Path;
use log::info;
use serde_json::Value;

pub(crate) enum GameType {
    CLASSIC,
    ARAM
}

pub(crate) fn setup_folder(path_name: String) -> bool {
    return if Path::new(&path_name).exists() {
        true
    } else {
        fs::create_dir(&path_name).expect("Could not setup folder!");
        false
    }
}

pub(crate) fn write_game_json_to_disk(parsed: Value, gt: GameType) {
    let file_prefix: String;
    match gt {
        GameType::CLASSIC => {
            file_prefix = "games/classic/".parse().unwrap();
        }
        GameType::ARAM => {
            file_prefix = "games/aram/".parse().unwrap();
        }
    }
    let file_path: String = file_prefix.as_str().to_owned() + parsed["metadata"]["matchId"].to_string().trim_matches('\"').to_owned().as_str() + ".json";
    let mut file = File::create(file_path.clone()).expect("Error while file write!");
    let f_json = serde_json::to_string_pretty(&parsed).expect("Error while formatting JSON");
    file.write_all(f_json.as_bytes()).expect("Error while writing json to file!");
    info!("{} Game written to {}!", parsed["metadata"]["matchId"], file_path);
}