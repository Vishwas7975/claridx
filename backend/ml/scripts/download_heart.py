from ml.datasets.heart import download, sha256_of


def main() -> None:
    path = download()
    print(f"Saved:   {path}")
    print(f"SHA-256: {sha256_of(path)}")


if __name__ == "__main__":
    main()
