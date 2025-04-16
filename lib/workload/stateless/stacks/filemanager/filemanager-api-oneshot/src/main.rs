use std::io;
use tokio::main;

#[tokio::main]
async fn main() -> io::Result<()> {
    println!("Hello world!");
    Ok(())
}
