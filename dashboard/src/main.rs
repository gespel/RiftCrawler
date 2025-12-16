#[macro_use] extern crate rocket;

#[get("/")]
fn index() -> &'static str {
    "Welcome to the RiftCrawler Dashboard!"
}

#[launch]
fn start() -> _ {
    rocket::build().mount("/", routes![index])
}
