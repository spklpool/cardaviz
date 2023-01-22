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

#[get("/hello/<name>")]
fn hello(name: &str) -> String {
    format!("Hello, {}!", name)
}

#[get("/pools/<ticker>")]
fn templated(ticker: &str) -> Template {
    Template::render("perfchart", context! { ticker: ticker })
}

#[get("/")]
fn index() -> Template {
    Template::render("pool_search", context! { })
}

#[launch]
fn rocket() -> _ {
    rocket::build().attach(Template::fairing())
        .mount("/", routes![index, hello, templated])
        .mount("/static", FileServer::from("./static"))
        .mount("/data", FileServer::from("./data"))
}

