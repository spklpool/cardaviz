#[macro_use] extern crate rocket;
use rocket_dyn_templates::{Template, context};
use std::fs;

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

#[get("/templated")]
fn templated() -> Template {
    let contents = fs::read_to_string("data/SPKL.json")
        .expect("Should have been able to read the file");
    let the_file = r#"{
        "FirstName": "John",
        "LastName": "Doe",
        "Age": 43,
        "Address": {
            "Street": "Downing Street 10",
            "City": "London",
            "Country": "Great Britain"
        },
        "PhoneNumbers": [
            "+44 1234567",
            "+44 2345678"
        ]
    }"#;

    let json: serde_json::Value =
        serde_json::from_str(&*contents).expect("JSON was not well-formatted");
    Template::render("perfchart", json)
}



#[launch]
fn rocket() -> _ {
    rocket::build().attach(Template::fairing())
        .mount("/", routes![index, hello, templated])
}

