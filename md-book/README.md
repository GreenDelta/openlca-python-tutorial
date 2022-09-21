# Install mdBook

[mdBook](https://rust-lang.github.io/mdBook/) is a utility to create modern online books from Markdown files. It is written in [Rust](https://www.rust-lang.org/), hence, easy to install with Rust and Cargo.

## Install Rust and Cargo on Windows

On Windows, download and run [rustup-init.exe](https://win.rustup.rs/). It will start the installation in a console and present the following message on success:

```bash
Rust is installed now. Great!
```

## Install Rust and Cargo on Mac and Linux

curl https://sh.rustup.rs -sSf | sh

It will download a script, and start the installation. If everything goes well, you’ll see this appear:

```bash
Rust is installed now. Great!
```

## Install mdBook

Once you have installed Rust, the following command can be used to build and install mdBook:

```bash
cargo install mdbook
```


# Run the server locally

Once in the mdBook folder run:

```bash
mdbook serve --open
```

This will open a new tab in your browser. The content of the mdBook is automatically updated after any changes.

# Build the documentation

Run the build command in the same directory where the `book.toml` file is located:

```bash
mdbook build
```