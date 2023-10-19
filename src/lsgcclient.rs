struct LSGCClient {
    pulls_this_second: i32,
    pulls_last_two_minutes: i32,
    client: reqwest::Client
}