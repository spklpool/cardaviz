#[macro_use] extern crate rocket;
use rocket_dyn_templates::{Template, context};
use std::fs;
use rocket::fs::FileServer;

#[cfg(test)]
mod tests {
    #[test]
    fn internal() {
        assert_eq!(4, 2 + 2);
    }
}

#[get("/")]
fn index() -> &'static str {
    "Hello, world!"
}

#[get("/hello/<name>")]
fn hello(name: &str) -> String {
    format!("Hello, {}!", name)
}

#[get("/pools/<ticker>")]
fn templated(ticker: &str) -> Template {
    let contents = fs::read_to_string("data/SPKL.json")
        .expect("Should have been able to read the file");
    let json: serde_json::Value =
        serde_json::from_str(&*contents).expect("JSON was not well-formatted");
    Template::render("perfchart", context! { ticker: ticker })
}



#[launch]
fn rocket() -> _ {
    rocket::build().attach(Template::fairing())
        .mount("/", routes![index, hello, templated])
        .mount("/static", FileServer::from("./static"))
        .mount("/data", FileServer::from("./data"))
}

