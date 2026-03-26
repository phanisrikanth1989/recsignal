# DB Agent Deployment Steps

## 1. Deploy the agent

```bash
cp -r agent/ /opt/recsignal/
```

## 2. Edit db_instances.cfg with real DB details

```bash
vi /opt/recsignal/config/db_instances.cfg
```

## 3. Set up your password script

```bash
cp /opt/recsignal/scripts/get_db_password.sh /opt/recsignal/bin/
chmod 700 /opt/recsignal/bin/get_db_password.sh

# Edit it with your actual credential-store logic
vi /opt/recsignal/bin/get_db_password.sh
```

## 4. Test password script manually

```bash
/opt/recsignal/bin/get_db_password.sh ORCL_UAT1 recsignal_mon
```

## 5. Update backend URL in db_config.yaml to point to your backend host

```bash
vi /opt/recsignal/config/db_config.yaml
```

## 6. Single test run (no loop)

```bash
cd /opt/recsignal
python db_agent.py
```

## 7. Continuous mode

```bash
python db_agent.py --loop --interval 30
```

## 8. For the server monitoring agent

```bash
python agent.py
```
