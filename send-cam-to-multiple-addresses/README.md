# Distribute CAM to Multiple Addresses

## Install requirements

```
pip install -r requirements.txt
```

## Rename and update config file

**Rename config example file**

```
cp config.yaml.example config.yaml
```

**Edit `config.yaml`:**

Edit file and add your address and private key.

## Create addresses and amounts file

Create a file that will have addresses and amounts for each address. One entry per line and separated by space.

**Syntax**:

```
<address1> <amount1>
<address2> <amount2>
<address3> <amount3>
<address4> <amount4>
```

**Example**:

```
0x4eF1b67228b56Df3Eda9A62Fe4331D1E74Ff1A2B 4
0x8cA2c67228b56Df3Eda9A62Fe4331D1E74Ff2B3C 4
0x7aD3d67228b56Df3Eda9A62Fe4331D1E74Ff3C4D 4
0x5bE4e67228b56Df3Eda9A62Fe4331D1E74Ff4D5E 4
0x3dF5f67228b56Df3Eda9A62Fe4331D1E74Ff5E6F 4
0x2cG6g67228b56Df3Eda9A62Fe4331D1E74Ff6F7G 4
0x1aH7h67228b56Df3Eda9A62Fe4331D1E74Ff7G8H 4
0x0bI8i67228b56Df3Eda9A62Fe4331D1E74Ff8H9I 4
0x9eJ9j67228b56Df3Eda9A62Fe4331D1E74Ff9I0J 4
0x8cK0k67228b56Df3Eda9A62Fe4331D1E74Ff0J1K 4
```

## Run the script

Replace options with chosen network and account from the config file and the addresses file

```
python distribute-cam.py distribute --network <network> --account <account> --addresses-file <addresses-file>
```