#[macro_use] extern crate rocket;
use rocket_db_pools::{sqlx, Database};
use rocket_db_pools::Connection;
use rocket_db_pools::sqlx::Row;
use rocket_dyn_templates::{Template, context};
use rocket::fs::FileServer;

#[cfg(test)]
mod tests {
    #[test]
    fn internal() {
        assert_eq!(4, 2 + 2);
    }
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
    rocket::build()
        .attach(Template::fairing())
        .mount("/", routes![index, hello, templated, latestepoch])
        .mount("/static", FileServer::from("./static"))
        .mount("/data", FileServer::from("./data"))
    load_pools_from_json();
}