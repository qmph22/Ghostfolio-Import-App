# Ghostfolio Import App

## Getting started

1. Clone the files and change directory into the new directory.
2. Place your root certificate chain in the following file path: `importapp/rootcertchain.pem`.
3. Prepare the the `allocations.yml` file that will contain the transactions to import.
   - Run `cp allocations.example.yml allocations.yml` to copy the `allocations.example.yml` to a working file.
   - Find all of the account IDs that you want to import transactions to. This can be done by going to Ghostfolio -> Accounts -> Click the account -> look in the URL after `accounts?accountId=`.
   - Modify the `allocations.yml` file to what you want to upload. Use the account IDs from the previous step.
   - Holdings specifies the stocks and the ratios that each contribution will go to each stock. The ratios must add up to 1.0.
4. Prepare the `.env` file.
   - Run `copy example.env .env` to copy the `example.env` file to a working file.
   - Get your Ghostfolio API key with `curl -X POST https://GHOSTFOLIOURLHERE/api/v1/auth/anonymous -H 'Content-Type: application/json' -d '{ "accessToken": "SECURITY_TOKEN_OF_ACCOUNT" }' -k` replacing `GHOSTFOLIOURLHERE` and `SECURITY_TOKEN_OF_ACCOUNT`.
   - Modify the `.env` file with the information from the previous step.
5. Create Python virtual environment.
   - Run `python -m venv .venv`   
   - Run `source .venv/bin/activate` to activate the Python virtual environment.
   - Run `app.py` with `python3 app.py`.
   - Run `pip install -r requirements.txt`.
   - Run `python3 app.py`
