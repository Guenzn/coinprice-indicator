# -*- coding: utf-8 -*-

# Bittrex
# https://bittrex.com/Home/Api

__author__ = "wizzard94@github.com"

from gi.repository import GLib

import requests
import logging

import utils
from exchange.error import Error
from alarm import Alarm

CONFIG = {
  'ticker': 'https://bittrex.com/api/v1.1/public/getmarketsummary',
  'asset_pairs': [
    {
      'isocode': 'XXBTZUSD',
      'pair': 'USDT-BTC',
      'name': 'BTC to USD',
      'currency': utils.currency['usd']
    },
    {
      'isocode': 'XXLTZUSD',
      'pair': 'USDT-LTC',
      'name': 'LTC to USD',
      'currency': utils.currency['usd']
    },
    {
      'isocode': 'XXETZUSD',
      'pair': 'USDT-ETH',
      'name': 'ETH to USD',
      'currency': utils.currency['usd']
    },
    {
      'isocode': 'XXBCZBTC',
      'pair': 'BTC-BCC',
      'name': 'BCC to BTC',
      'currency': utils.currency['btc']
    },
    {
      'isocode': 'XXETZBTC',
      'pair': 'BTC-ETH',
      'name': 'ETH to BTC',
      'currency': utils.currency['btc']
    },
    {
      'isocode': 'XXRPZBTC',
      'pair': 'BTC-XRP',
      'name': 'XRP to BTC',
      'currency': utils.currency['btc']
    },
    {
      'isocode': 'XXMRZBTC',
      'pair': 'BTC-XMR',
      'name': 'XMR to BTC',
      'currency': utils.currency['btc']
    }
  ]
}

class Bittrex:

  def __init__(self, config, indicator):
    self.indicator = indicator

    self.timeout_id = 0
    self.alarm = Alarm(config['app']['name'])

    self.error = Error(self)

  def start(self, error_refresh=None):
    refresh = error_refresh if error_refresh else self.indicator.refresh_frequency
    self.timeout_id = GLib.timeout_add_seconds(refresh, self.check_price)

  def stop(self):
    if self.timeout_id:
      GLib.source_remove(self.timeout_id)

  def check_price(self):
    self.asset_pair = self.indicator.active_asset_pair

    self.pair = [item['pair'] for item in CONFIG['asset_pairs'] if item['isocode'] == self.asset_pair][0]

    try:
      res = requests.get(CONFIG['ticker'] + '?market=' + self.pair)
      data = res.json()

      if not data['success']:
        self._handle_error(data['error'])
      elif data['result']:
        self._parse_result(data['result'])

    except Exception as e:
      logging.info('Error: ' + str(e))
      self.error.increment()

    return self.error.is_ok()

  def _parse_result(self, data):
    self.error.clear()

    '''
    Response example
    [{'Bid': 5655.15, 'MarketName': 'USDT-BTC', 'Ask': 5665.0, 'BaseVolume': 19499585.87469274, 'High': 5888.0, 'Low': 5648.0, 'Volume': 3393.61801172, 'OpenBuyOrders': 8505, 'Created': '2015-12-11T06:31:40.633', 'PrevDay': 5762.180121, 'Last': 5665.0, 'OpenSellOrders': 4194, 'TimeStamp': '2017-10-28T12:24:39.38'}]
    '''

    asset = data[0]

    currency = [item['currency'] for item in CONFIG['asset_pairs'] if item['isocode'] == self.asset_pair][0]

    coin = [item['name'] for item in CONFIG['asset_pairs'] if item['isocode'] == self.asset_pair][0]

    label = currency + utils.decimal_auto(asset['Last'])

    bid = utils.category['bid'] + currency + utils.decimal_auto(asset['Bid'])
    high = utils.category['high'] + currency + utils.decimal_auto(asset['High'])
    low = utils.category['low'] + currency + utils.decimal_auto(asset['Low'])
    ask = utils.category['ask'] + currency + utils.decimal_auto(asset['Ask'])

    self.indicator.set_data(label, bid, high, low, ask)

  def _handle_error(self, error):
    logging.info("Bittrex API error: " + error[0])
