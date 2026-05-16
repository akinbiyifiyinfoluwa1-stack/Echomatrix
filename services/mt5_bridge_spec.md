# MT5 Bridge Spec

Echo Matrix backend (Ubuntu) communicates with a Windows-hosted MT5 bridge service.

## Contract
- Backend -> `POST /orders` with normalized order payload.
- Bridge authenticates using bearer token.
- Bridge translates payload to MT5 terminal commands.
- Bridge returns order ticket, status, and execution metadata.

This abstraction allows future multi-broker adapters (IBKR, OANDA, Binance Futures).
