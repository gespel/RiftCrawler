FROM rust:latest

WORKDIR /app

COPY . .

RUN cargo build --release

ENV RUST_LOG=debug

ENTRYPOINT ["./target/release/riftcrawler"]
