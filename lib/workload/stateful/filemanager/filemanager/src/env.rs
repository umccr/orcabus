use std::{
    env,
    fmt::{self},
};

use dotenvy;
use tracing::{error, info};

/// Controls environment.
#[derive(PartialEq)]
pub enum AppEnv {
    /// Dev environment loads config from dotenv.
    Dev,
    /// Prod environment doesn't load local dotenv config.
    Prod,
}

/// Determines whether we are in production or development mode
/// based on .env and/or APP_ENV environment variable
pub fn load_env() -> AppEnv {
    let app_env = match env::var("APP_ENV") {
        Ok(v) if v == "prod" => AppEnv::Prod,
        _ => AppEnv::Dev,
    };

    info!("Running in {app_env} mode");

    if app_env == AppEnv::Dev {
        match dotenvy::dotenv() {
            Ok(path) => info!(".env read successfully from {}", path.display()),
            Err(e) => error!("Could not load .env file: {e}"),
        };
    };

    app_env
}

impl fmt::Display for AppEnv {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppEnv::Dev => write!(f, "dev"),
            AppEnv::Prod => write!(f, "prod"),
        }
    }
}
