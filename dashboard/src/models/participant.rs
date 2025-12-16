use rocket::serde::{Serialize};

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub struct Participant {
    pub all_in_pings: u32,
    pub assist_me_pings: u32,
    pub assists: u32,
    pub bait_pings: u32,
    pub baron_kills: u32,
    pub basic_pings: u32,
    pub bounty_level: u32,
    pub challenges: Challenges,
    pub champ_experience: u32,
    pub champ_level: u32,
    pub champ_id: u32,
    pub champion_name: String,
    pub champion_transform: u32,
    pub command_pings: u32,
    pub consumables_purchased: u32,
    pub damage_dealt_to_buildings: u32,
    pub damage_dealt_to_objectives: u32,
    pub damage_dealt_to_turrets: u32,
    pub damage_self_mitigated: u32,
    pub danger_pings: u32,
    pub deaths: u32,
    pub detector_wards_placed: u32,
    pub double_kills: u32,
    pub dragon_kills: u32,
    pub eligible_for_progression: bool,
    pub enemy_missing_pings: u32,
    pub enemy_vision_pings: u32,
    pub first_blood_assist: bool,
    pub first_blood_kill: bool,
    pub first_tower_assist: bool,
    pub first_tower_kill: bool,
    pub game_ended_in_early_surrender: bool,
    pub game_ended_in_surrender: bool,
    pub get_back_pings: u32,
    pub gold_earned: u32,
    pub gold_spent: u32,
    pub hold_pings: u32,
    pub individual_position: String,
    pub inhibitor_kills: u32,
    pub inhibitor_takedowns: u32,
    pub inhibitors_lost: u32,
    pub item0: u32,
    pub item1: u32,
    pub item2: u32,
    pub item3: u32,
    pub item4: u32,
    pub item5: u32,
    pub item6: u32,
    pub items_purchased: u32,
    pub killing_sprees: u32,
    pub kills: u32,
    pub lane: String,
    pub largest_critical_strike: u32,
    pub largest_killing_spree: u32,
    pub longest_time_spent_living: u32,
    pub magic_damage_dealt: u32,
    pub magic_damage_dealt_to_champions: u32,
    pub magic_damage_taken: u32,
    pub missions: Missions,
    pub need_vision_pings: u32,
    pub neutral_minions_killed: u32,
    
}

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub struct Challenges {

}

#[derive(Serialize)]
#[serde(crate = "rocket::serde")]
pub struct Missions {

}