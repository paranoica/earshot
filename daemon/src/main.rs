use std::process::ExitCode;

const USAGE: &str = "Usage: earshot-daemon [--version | --help]

Options:
  -V, --version  Print the version and exit
  -h, --help     Print this help and exit
";

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.iter().map(String::as_str).collect::<Vec<_>>().as_slice() {
        ["--version" | "-V"] => {
            println!("earshot-daemon {}", env!("CARGO_PKG_VERSION"));
            ExitCode::SUCCESS
        }
        ["--help" | "-h"] => {
            print!("{USAGE}");
            ExitCode::SUCCESS
        }
        _ => {
            eprint!("{USAGE}");
            ExitCode::from(2)
        }
    }
}
