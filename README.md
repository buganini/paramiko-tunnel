# Paramiko Tunnel

This article demonstrates how to use `Paramiko` as both an SSH client and server, enabling secure communication between systems without requiring host machines to provide or expose native SSH services. This approach offers flexibility and control over SSH functionality in various environments, such as IoT device management.

[Paramiko](https://www.paramiko.org/) is a pure-Python 1 (3.6+) implementation of the SSHv2 protocol 2, providing both client and server functionality.

## SSH Tunnel

### Local Port Forwarding
```mermaid
sequenceDiagram
    participant Friend Of Client
    participant SSH Client
    participant SSH Server
    participant Friend Of Server
    SSH Client->>SSH Server: Connect
    Note over SSH Client,SSH Server: SSH Connection Establish
    Note over SSH Client: Bind Local Port
    SSH Client->>Friend Of Server: Tunneled Traffic
```

### Remote Port Forwarding
```mermaid
sequenceDiagram
    participant Friend Of Client
    participant SSH Client
    participant SSH Server
    participant Friend Of Server
    SSH Client->>SSH Server: Connect
    Note over SSH Client,SSH Server: SSH Connection Establish
    Note over SSH Server: Bind Remote Port
    SSH Server->>Friend Of Client: Tunneled Traffic
```


## Paramiko Tunnel

The following example uses `Remote Port Forwarding` to enable a controller to access a terminal device's SSH via Out-of-Band (OOB) communication, such as MQTT.

```mermaid
sequenceDiagram
    participant OOB
    participant Terminal (SSH Client)
    participant Controller (SSH Server)
    Terminal (SSH Client)->>OOB: Connect
    Note over Controller (SSH Server): Create SSH Service
    Controller (SSH Server)->>OOB: Service Information and Connect Request
    OOB->>Terminal (SSH Client): Service Information and Connect Request
    Terminal (SSH Client)->>Controller (SSH Server): Connect
    Note over Controller (SSH Server): Bind Remote Port
    Controller (SSH Server)->>Terminal (SSH Client): Tunneled Traffic to Terminal's Host SSH
```

First, start the controller and create a SSH service
```
> python3 controller.py
[*] Bind Success for SSH Server using 0.0.0.0:52412
[*] Listening
```

```
```