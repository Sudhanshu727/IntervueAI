def main(x):
    total = 0
    for i in range(x * 10000):  # Make it more computationally intensive
        total += i
    print(f"Sum for {x * 10000} iterations: {total}")

if __name__ == "__main__":
    main(100)