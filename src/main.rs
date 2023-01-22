#[macro_use] extern crate rocket;
use rocket_db_pools::{sqlx, Database};
use rocket_db_pools::Connection;
use rocket_db_pools::sqlx::Row;
use rocket_dyn_templates::{Template, context};
use rocket::fs::FileServer;

#[derive(Database)]
#[database("cexplorer")]
struct CExplorer(sqlx::PgPool);

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

#[get("/latestepoch")]
async fn latestepoch(mut db: Connection<CExplorer>) -> String {
    let epochrow = sqlx::query("SELECT MAX(NO) as latest_epoch FROM epoch;")
        .fetch_one(&mut *db).await
        .expect("failed getting the latest epoch from the database");
    let epoch: i32 = epochrow.get(0);
    format!("latest epoch: {}", epoch)
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
        .attach(CExplorer::init())
        .mount("/", routes![index, hello, templated, latestepoch])
        .mount("/static", FileServer::from("./static"))
        .mount("/data", FileServer::from("./data"))
}