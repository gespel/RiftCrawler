use tokio::time::{sleep, Duration};
use reqwest::header::HeaderMap;
use reqwest::Client;

pub struct LSGCClient {
    pulls_this_second: i32,
    pulls_last_two_minutes: i32,
    client: reqwest::Client,
    header: HeaderMap
}

impl LSGCClient {
    pub fn new(api_key: String) -> LSGCClient {
        let mut hm = HeaderMap::new();
        hm.insert("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36".parse().unwrap());
        hm.insert("Accept-Language", "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7".parse().unwrap());
        hm.insert("Accept-Charset", "application/x-www-form-urlencoded; charset=UTF-8".parse().unwrap());
        hm.insert("Origin", "http://sten-heimbrodt.de/lolstats".parse().unwrap());
        hm.insert("X-Riot-Token", "RGAPI-3997e725-ff9a-4b69-8d12-58913508fdd0".parse().unwrap());

        let out = LSGCClient {
            pulls_this_second: 0,
            pulls_last_two_minutes: 0,
            client: reqwest::Client::new(),
            header: hm,
        };
        return out;
    }
    pub async fn request(&mut self, uri: String) -> Result<String, reqwest::Error> {
        self.pulls_this_second += 1;
        self.pulls_last_two_minutes += 1;

        if self.pulls_this_second >= 19 {
            sleep(Duration::from_secs(1)).await;
            self.pulls_this_second = 0;
        }

        if self.pulls_last_two_minutes >= 99 {
            sleep(Duration::from_secs(100)).await;
        }

        let h = &self.header;
        let response = self.client
            .get(uri)
            .headers(h.clone())
            .send()
            .await?;

        if response.status().is_success() {
            println!("{} Request was successful", self.pulls_last_two_minutes);
        } else {
            println!("Request failed with status code: {}", response.status());
        }

        Ok(response.text().await?)
    }
}
