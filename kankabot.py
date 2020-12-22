#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://github.com/Fallayn/kanka-discord
#
# Post new Kanka updates to Discord using the Kanka API and Discord webhooks
#
# Based on the Python Kanka API work done by Poolitzer at
#  https://github.com/Poolitzer/kanka
#
# Thanks for that! You at least want to change these below:
# secret, discord_channel_log, discord_channel_post, campaign_name, campaign_id
#
# Requires Python 3
# Licensed under GPL 3

# TODO: Handle large number of updated entities since last run - summarize

import kanka
import requests
import json
import re
import dateutil.parser
import time
import os
import traceback

secret = "<YOUR KANKA API KEY HERE>"

discord_channel_log = "<LOG DISCORD CHANNEL WEBHOOK URL>"
discord_channel_post = "<LOG DISCORD CHANNEL WEBHOOK URL>"
discord_enabled = True
discord_log_enabled = True
discord_name = "Kanka"
discord_length = 180

lang = "en"
campaign_id = <YOUR CAMPAIGN ID HERE>
campaign_name = "<YOUR CAMPAIGN NAME>"
ignore_before = "2020-12-01T12:00:00.000000Z"

title_hide_list = ["private", "hidden", "secret"]

default_user_icon = "https://kanka.io/images/defaults/user.svg"

poll_interval_seconds = 30
error_count_max = 5
force_sync = False
ignore_same_id = True
use_colors = True
use_footer = False
exclude_private = True
exclude_template = True

url = f"campaigns/{int(campaign_id)}/"
full_url = f"https://kanka.io/{lang}/campaign/{int(campaign_id)}/"
last_id = -1
users = []
latest_update = ""
dir_path = os.path.dirname(os.path.realpath(__file__))
last_update_path = f"{dir_path}/last_update.txt"

default_thumbs = {
  "character": "https://kanka.io/images/defaults/patreon/characters_thumb.png",
  "location": "https://kanka.io/images/defaults/patreon/locations_thumb.png",
  "journal": "https://kanka.io/images/defaults/patreon/journals_thumb.png",
  "timeline": "https://kanka.io/images/defaults/patreon/timelines_thumb.png",
  "family": "https://kanka.io/images/defaults/patreon/families_thumb.png",
  "organisation": "https://kanka.io/images/defaults/patreon/organisations_thumb.png",
  "item": "https://kanka.io/images/defaults/patreon/items_thumb.png",
  "note": "https://kanka.io/images/defaults/patreon/notes_thumb.png",
  "event": "https://kanka.io/images/defaults/patreon/events_thumb.png",
  "calendar": "https://kanka.io/images/defaults/patreon/calendars_thumb.png",
  "race": "https://kanka.io/images/defaults/patreon/races_thumb.png",
  "quest": "https://kanka.io/images/defaults/patreon/quests_thumb.png",
  "map": "https://kanka.io/images/defaults/patreon/maps_thumb.png",
  "ability": "https://kanka.io/images/defaults/patreon/abilities_thumb.png",
  "tag": "https://kanka.io/images/defaults/patreon/tags_thumb.png",
  "conversation": "https://kanka.io/images/defaults/patreon/conversations_thumb.png",
  "dice_roll": "https://kanka.io/images/defaults/patreon/dice_rolls_thumb.png"
}

plural = {
  "character": "characters",
  "location": "locations",
  "journal": "journals",
  "timeline": "timelines",
  "family": "families",
  "organisation": "organisations",
  "item": "items",
  "note": "notes",
  "event": "events",
  "calendar": "calendars",
  "race": "races",
  "quest": "quests",
  "map": "maps",
  "ability": "abilities",
  "tag": "tags",
  "conversation": "conversations",
  "dice_roll": "dice_rolls"
}

title = {
  "character": "Character",
  "location": "Location",
  "journal": "Journal",
  "timeline": "Timeline",
  "family": "Family",
  "organisation": "Organisation",
  "item": "Item",
  "note": "Note",
  "event": "Event",
  "calendar": "Calendar",
  "race": "Race",
  "quest": "Quest",
  "map": "Map",
  "ability": "Ability",
  "tag": "Tag",
  "conversation": "Conversation",
  "dice_roll": "Dice Roll"
}

colors = {
  "character": 2040620,
  "location": 10593446,
  "journal": 6839373,
  "timeline": 11052711,
  "family": 4926797,
  "organisation": 1447446,
  "item": 2370874,
  "note": 9143921,
  "event": 2299414,
  "calendar": 1447446,
  "race": 3947631,
  "quest": 5325616,
  "map": 6530438,
  "ability": 10427931,
  "tag": 6380101,
  "conversation": 4742238,
  "dice_roll": 1052688
}

def main():
  global users
  
  try:
    with open(last_update_path, "r", encoding="utf-8") as input:
      global latest_update
      latest_update = input.read().strip()
  except FileNotFoundError:
    pass
  
  login(force_sync)

  users = fetch_users()
  
  error_count = 0
  while True:
    try:
      poll_updates()
      time.sleep(poll_interval_seconds)
      error_count = 0
    except KeyboardInterrupt:
      break
    except Exception as e:
      error_count += 1
      if error_count > error_count_max:
        error_count = error_count_max
      
      msg = traceback.format_exc()
      
      if discord_log_enabled:
        try:
          discord(discord_channel_log, discord_name, "ERROR: ```" + msg + "```")
        except KeyboardInterrupt:
          break
        except:
          pass
      
      time.sleep(poll_interval_seconds * error_count)
      continue

def poll_updates():
  global last_id
  global users
  
  set_sync = True
  entities = fetch_updated_entities(set_sync)
  
  embeds = []
  for entity in entities:
    entity_id = entity["id"]
    
    if ignore_same_id and entity_id == last_id:
      continue
    last_id = entity_id
    
    description = ""
    
    if "type" in entity and "child_id" in entity:
      child_id = entity["child_id"]
      if entity["type"] in plural:
        p = plural[entity["type"]]
        data = get(f"{p}/{child_id}")
        if data and len(data) > 0:
          if "entry" in data:
            description = str(data["entry"])
    
    description = re.sub('<[^<]+?>', '', description)
    description = re.sub('\[[0-9a-z]+:[0-9]+\]', '...', description)
    description = shorten(description, discord_length)
    
    name = "Unknown"
    if "name" in entity:
      if len(entity["name"]) > 0:
        name = entity["name"]
      
      hide = False
      for word in title_hide_list:
        if word in name.lower():
          hide = True
          break
      
      if hide:
        continue
    
    user_name = "Unknown"
    user_icon = ""
    if "updated_by" in entity:
      user_id = entity["updated_by"]
      if not user_id in users:
        users = fetch_users()
      if user_id in users:
        user_name = users[user_id]["name"]
        user_icon = users[user_id]["avatar"]
        if len(user_icon) < 1 or user_icon.endswith("user.svg"):
          user_icon = default_user_icon
    
    embed = {}
    embed["title"] = name
    if "type" in entity:
      entity_type = entity["type"]
      if entity_type in title:
        embed["title"] = title[entity_type] + " » " + name
    
    description = str(description)
    if len(description) > 0 and description != "None":
      embed["description"] = description
    
    embed["url"] = full_url
    if "type" in entity and "child_id" in entity:
      entity_type = entity["type"]
      if entity_type in plural:
        embed["url"] = full_url + plural[entity_type] + "/" + str(entity["child_id"])
    
    if use_colors and "type" in entity and entity["type"] in colors:
      embed["color"] = colors[entity["type"]]
    
    if use_footer and "updated_at" in entity:
      embed["timestamp"] = entity["updated_at"]
    
    author = {}
    author["name"] = user_name
    author["url"] = embed["url"]
    author["icon_url"] = user_icon
    embed["author"] = author
    
    thumbnail = {}
    thumbnail["url"] = default_user_icon
    
    entity_icon = ""
    entity_type = ""
    if "type" in entity:
      entity_type = entity["type"]
    
    if len(entity_type) > 0 and entity_type in default_thumbs:
      entity_icon = default_thumbs[entity_type]
      thumbnail["url"] = entity_icon
    
    if "header_image" in entity and entity["header_image"]:
      thumb_url = entity["header_image"]
      if len(thumb_url) > 0:
        thumbnail["url"] = thumb_url
    embed["thumbnail"] = thumbnail
    
    footer = {}
    footer["icon_url"] = default_user_icon
    if len(entity_icon) > 0:
      footer["icon_url"] = entity_icon
    footer["text"] = campaign_name
    
    if use_footer:
      embed["footer"] = footer
    
    embeds.append(embed)
    
  discord(discord_channel_post, discord_name, "", embeds)

def fetch_updated_entities(sync=False):
  out = []
  entities = get("entities", sync)
  
  ignore_updates_before = latest_update

  for entity in entities:
    if "is_private" in entity and entity["is_private"] and exclude_private:
      continue
    
    if "is_template" in entity and entity["is_template"] and exclude_template:
      continue
    
    if "updated_at" in entity:
      update(entity["updated_at"])
      
      if len(ignore_updates_before) > 0 and len(entity["updated_at"]) > 0:
        if entity["updated_at"].strip() <= ignore_updates_before:
          continue
      
      updated = dateutil.parser.isoparse(entity["updated_at"])
      ignore_before_date = dateutil.parser.isoparse(ignore_before)
      if updated < ignore_before_date:
        continue
    
    out.append(entity)
  
  return out

def update(date):
  if len(date) < 1:
    return
  
  global latest_update
  if len(latest_update) < 1 or date > latest_update:
    latest_update = date
  
  try:
    with open(last_update_path, "w", encoding="utf-8") as out:
      out.write(date.strip())
  except:
    traceback.print_exc()

def shorten(text, length):
  if not text or len(str(text)) < 1 or text == "None":
    return ""
  
  out = ""
  shortened = True
  
  if len(text) > length:
    parts = text.split()
    
    for part in parts:
      if len(out) < 1:
        out = out + part
        if len(out) > length:
          out = out[:length]
          break
        continue
      
      out_new = out + " " + part
      if len(out_new) > length:
        break
      out = out_new
  else:
    out = text
    shortened = False
  
  out = out.strip()
  out = out.strip(".")
  out = out.strip()
  
  if shortened:
    out = out + "..."
  else:
    if not out.endswith(".") and not out.endswith("?") and not out.endswith("!"):
      out = out + "..."
  
  return out

def fetch_users(sync=False):
  users = {}
  user_data = get("users", sync)
  if len(user_data) < 1:
    raise RuntimeError("No users found")
  
  for user in user_data:
    if not "id" in user or user["id"] < 0:
      raise RuntimeError("User missing or invalid ID")
    
    if not "name" in user or len(user["name"]) < 1:
      raise RuntimeError("User missing name: " + user["id"])
    
    users[user["id"]] = user
  
  return users

def get(route, sync=False):
  req_url = url + route
  
  if force_sync:
    sync = True
  
  raw = kanka._get(req_url, sync=sync)
  if not "data" in raw:
    raise RuntimeError("Missing data for route " + req_url)
  return raw["data"]

def login(sync):
    kanka.login(secret, sync)

def discord(url, user, message, embeds = []):
  if not discord_enabled:
    return
  
  # for all params, see
  # https://discordapp.com/developers/docs/resources/webhook#execute-webhook
  # https://discord.com/developers/docs/resources/channel#embed-object
  
  data = {}
  data["content"] = message
  data["username"] = user

  if embeds and len(embeds) > 0:
    data["embeds"] = embeds

  result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
  return result

if __name__ == "__main__":
  main()