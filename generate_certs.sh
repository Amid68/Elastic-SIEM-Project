mkdir -p elasticsearch/certs
cd elasticsearch/certs

# Generate CA
openssl req -x509 -nodes -newkey rsa:2048 -keyout ca.key -out ca.crt -days 365 -subj "/CN=Elastic-CA"

# Generate server certificate
openssl req -nodes -newkey rsa:2048 -keyout node.key -out node.csr -subj "/CN=elasticsearch"
openssl x509 -req -in node.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out node.crt -days 365
