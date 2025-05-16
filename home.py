from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Input, Button, ListView, ListItem
from rpc import rpc_call
from rich.console import Console
console = Console()


# Just a quick wallet summary panel
class OverviewTab(Static):
    def on_mount(self):
        # Grab wallet + blockchain info on start
        wallet = rpc_call("getwalletinfo")
        balance = rpc_call("getbalance")
        chain_data = rpc_call("getblockchaininfo")

        # Compose display string
        info = f"""
Wallet Status: Active
Wallet Name: {wallet.get('walletname', 'Unknown')}
Network: {chain_data.get('chain', 'Unknown')}
Sync Status: {chain_data.get('blocks', 0)}/{chain_data.get('headers', 0)} blocks
Balance: {balance} BTC
Transaction Count: {wallet.get('txcount', 0)}
"""
        self.update(info)


class SendTab(Static):
    def compose(self) -> ComposeResult:
        # A simple sending form UI
        yield Static("Recipient Address:")
        self.to_input = Input(placeholder="myeFgAddr...")
        yield self.to_input

        yield Static("Amount (BTC):")
        self.amt_input = Input(placeholder="0.001")
        yield self.amt_input

        yield Button("Send", id="send-btn")

        self.feedback = Static("", classes="status hidden")
        yield self.feedback

    def on_button_pressed(self, event) -> None:
        if event.button.id != "send-btn":
            return

        try:
            # Validate inputs
            address = self.to_input.value
            amount_str = self.amt_input.value

            if not address:
                self.feedback.remove_class("hidden")
                self.feedback.update("[red]Error: Missing address![/red]")
                return

            if not amount_str:
                self.feedback.remove_class("hidden")
                self.feedback.update("[red]Error: No amount entered[/red]")
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    self.feedback.remove_class("hidden")
                    self.feedback.update("[red]Amount must be > 0[/red]")
                    return
            except ValueError:
                self.feedback.remove_class("hidden")
                self.feedback.update("[red]Amount should be a number[/red]")
                return

            current_balance = rpc_call("getbalance")
            if amount > current_balance:
                self.feedback.remove_class("hidden")
                self.feedback.update(f"[red]Not enough funds. You have {current_balance} BTC[/red]")
                return

            # Proceed with sending
            txid = rpc_call("sendtoaddress", [address, amount])
            self.feedback.remove_class("hidden")
            self.feedback.update(f"[green]Sent! TXID: {txid}[/green]")

        except Exception as err:
            self.feedback.remove_class("hidden")
            self.feedback.update(f"[red]Failed to send: {err}[/red]")


class ReceiveTab(Static):
    def on_mount(self):
        # Just fetch a fresh address
        try:
            addr = rpc_call("getnewaddress")
            self.update(f"New Address:\n{addr}")
        except Exception as err:
            if "No wallet loaded" in str(err):
                self.update("Please create a wallet first!")
            else:
                self.update(f"Error fetching address: {err}")


class TransactionsTab(Static):
    def compose(self):
        # Add refresh button and list view
        yield Button("Refresh", id="refresh-btn")
        self.tx_list = ListView()
        yield self.tx_list

    def on_mount(self):
        # Load transactions at startup
        self.load_transactions()

    def format_transaction(self, tx):
        # Break down transaction details for display
        from datetime import datetime

        amt = tx.get('amount', 0)
        cat = tx.get('category', 'unknown')
        txid = tx.get('txid', 'unknown')
        ts = tx.get('time', 0)
        confs = tx.get('confirmations', 0)
        fee = tx.get('fee', 0)
        addr = tx.get('address', 'unknown')

        time_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else 'Unknown'

        details = f"""
Category: {cat}
Amount: {amt} BTC
Date: {time_str}
Confirmations: {confs}
Address: {addr}
"""
        if fee:
            details += f"Fee: {fee} BTC\n"
        details += f"Transaction ID: {txid}"

        return details

    def load_transactions(self):
        try:
            console.print("[yellow]Loading transactions...[/yellow]")
            txs = rpc_call("listtransactions")

            if not txs:
                self.tx_list.clear()
                self.tx_list.append(ListItem(Static("No transactions found")))
                return

            txs.sort(key=lambda x: x.get('time', 0), reverse=True)

            self.tx_list.clear()
            for t in txs:
                self.tx_list.append(ListItem(Static(self.format_transaction(t))))
        except Exception as err:
            console.print(f"[red]Error loading txs: {err}[/red]")
            self.tx_list.clear()
            self.tx_list.append(ListItem(Static(f"Error: {err}")))

    def on_button_pressed(self, event):
        if event.button.id == "refresh-btn":
            self.load_transactions()


class WalletApp(App):
    CSS_PATH = "wallet.css"

    def compose(self):
        yield Header(name="Bitcoin Wallet App", show_clock=True)
        with TabbedContent():
            yield TabPane("Overview", OverviewTab())
            yield TabPane("Send", SendTab())
            yield TabPane("Receive", ReceiveTab())
            yield TabPane("Transactions", TransactionsTab())
        yield Footer()


if __name__ == "__main__":
    WalletApp().run()
