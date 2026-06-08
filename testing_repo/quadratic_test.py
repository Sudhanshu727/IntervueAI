def main(x):
    count = 0
    for i in range(x):
        for j in range(x):
                count += 1
    print(f"Processed {count} iterations for input {x}")

if __name__ == "__main__":
    main(50)