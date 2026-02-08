from tabulate import tabulate

def print_table(data):
    print(tabulate(data, headers="keys", tablefmt="grid"), "\n\n\n")
