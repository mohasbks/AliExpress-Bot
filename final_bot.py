import os
import asyncio
import json
import logging
import time
import hmac
import hashlib
import urllib.parse
import requests
import random
from datetime import datetime
from typing import Dict, Optional, List
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# AliExpress API Configuration
ALIEXPRESS_API_URL = "https://api-sg.aliexpress.com/sync"
APP_KEY = "511896"
APP_SECRET = "xe8oIZLMqCoPT4vCNMxiLcU78F7njsCl"

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8353510100:AAHPLe2dqKEdD0CAHROJiho1nrQWwj5ItgU')

# Multiple Admin User IDs - only these users can control the bot
ADMIN_USER_IDS = [5255786759, 5232979183, 990541]

# Multi-Channel Configuration with specific filters
CHANNELS_CONFIG = {
    'hot_deals': {
        'channel_id': '@HotFindsExpress',
        'name': 'Hot Finds & Deals',
        'active': True,
        'posting_interval': 105,  # minutes (~1h 45m) - Fast channel
        'min_price': 0,  # No minimum price filter
        'max_price': 1000,  # High max for variety
        'min_commission': 0,  # No commission filter - get everything!
        'keywords': [],  # No keywords - get all trending products!
        'exclude_keywords': ['fake', 'replica', 'used', 'broken']
    },
    'tech': {
        'channel_id': '@AliTechFinds',
        'name': 'Tech & Electronics',
        'active': True,
        'posting_interval': 180,  # minutes (3 hours) - Specialized channel
        'min_price': 5,
        'max_price': 200,
        'min_commission': 5,
        'keywords': ['phone', 'headphone', 'bluetooth', 'wireless', 'earphone', 'earbuds',
                    'cable', 'charger', 'adapter', 'usb', 'smart', 'watch', 'gadget',
                    'electronic', 'tech', 'pc', 'computer', 'mouse', 'keyboard', 'speaker',
                    'camera', 'led', 'power bank', 'tablet', 'laptop', 'monitor',
                    'smartphone', 'android', 'ios', 'iphone', 'samsung', 'xiaomi',
                    'headset', 'gaming', 'rgb', 'mechanical', 'webcam', 'microphone',
                    'earphones', 'airpods', 'tws', 'soundbar', 'subwoofer', 'amplifier',
                    'hub', 'dock', 'converter', 'splitter', 'extension', 'cord',
                    'lightning', 'type-c', 'micro usb', 'hdmi', 'displayport', 'vga',
                    'smartwatch', 'fitness', 'tracker', 'band', 'wearable',
                    'router', 'wifi', 'modem', 'repeater', 'extender', 'network',
                    'ssd', 'hard drive', 'storage', 'memory', 'ram', 'flash',
                    'gpu', 'graphics', 'cooling', 'fan', 'radiator', 'thermal',
                    'controller', 'joystick', 'gamepad', 'console', 'playstation', 'xbox',
                    'projector', 'tv box', 'streaming', 'media', 'player', 'chromecast',
                    'drone', 'quadcopter', 'gimbal', 'stabilizer', 'action cam', 'gopro',
                    'ring light', 'studio', 'lighting', 'tripod', 'mount', 'stand',
                    'laser', 'pointer', 'presenter', 'remote', 'clicker',
                    'scanner', 'printer', 'ink', 'toner', 'cartridge',
                    'telescope', 'microscope', 'binoculars', 'magnifier',
                    'soldering', 'multimeter', 'oscilloscope', 'tool kit',
                    'breadboard', 'arduino', 'raspberry pi', 'esp32', 'sensor', 'module',
                    'battery', 'portable', 'solar', 'generator', 'inverter',
                    'dashcam', 'car camera', 'parking', 'gps', 'navigator', 'radar',
                    'bluetooth speaker', 'portable speaker', 'mini speaker', 'bass',
                    'noise cancelling', 'anc', 'ambient', 'transparency',
                    'mechanical keyboard', 'backlit', 'macro', 'numpad',
                    'optical mouse', 'vertical mouse', 'trackball', 'touchpad',
                    'usb hub', 'card reader', 'otg', 'dongle',
                    'screen protector', 'tempered glass', 'case', 'cover', 'sleeve',
                    'stylus', 'pen', 'digital', 'drawing', 'graphics tablet',
                    'vr', 'virtual reality', 'ar', 'headset', 'glasses',
                    'smart home', 'automation', 'switch', 'plug', 'bulb', 'strip'],
        'exclude_keywords': ['fake', 'replica', 'used']
    },
    'home': {
        'channel_id': '@AliHomeEssentials',
        'name': 'Home, Kitchen & Car Essentials',
        'active': True,
        'posting_interval': 195,  # minutes (~3h 15m) - Specialized channel
        'min_price': 3,
        'max_price': 150,
        'min_commission': 4,
        'keywords': ['home', 'kitchen', 'storage', 'organizer', 'cleaning', 'tool', 'rack',
                    'holder', 'container', 'basket', 'shelf', 'hook', 'smart home', 'gadget',
                    'utensil', 'cookware', 'dish', 'bottle', 'cup', 'plate', 'bowl',
                    'drawer', 'box', 'bin', 'hanger', 'laundry', 'bathroom',
                    'car', 'vehicle', 'auto', 'dashboard', 'seat', 'steering', 'mirror',
                    'tire', 'vacuum', 'phone holder', 'charger car', 'air freshener',
                    'organizer car', 'mat', 'cover', 'accessories car',
                    # Kitchen expanded
                    'knife', 'cutting board', 'peeler', 'grater', 'slicer', 'chopper',
                    'spatula', 'turner', 'ladle', 'whisk', 'tongs', 'masher',
                    'strainer', 'colander', 'funnel', 'measuring', 'scale', 'timer',
                    'pot', 'pan', 'wok', 'skillet', 'frying', 'baking',
                    'oven', 'microwave', 'toaster', 'blender', 'mixer', 'processor',
                    'kettle', 'teapot', 'coffee', 'espresso', 'french press', 'grinder',
                    'can opener', 'bottle opener', 'corkscrew', 'jar', 'dispenser',
                    'food storage', 'lunch box', 'bento', 'thermos', 'insulated',
                    'cutting mat', 'apron', 'glove', 'mitt', 'trivet', 'coaster',
                    'sink', 'faucet', 'drain', 'soap', 'sponge', 'scrubber', 'cloth',
                    'garbage', 'trash', 'waste', 'compost', 'recycling',
                    # Home expanded
                    'curtain', 'blind', 'rod', 'drape', 'window', 'shade',
                    'cushion', 'pillow', 'throw', 'blanket', 'bedding', 'sheet',
                    'duvet', 'comforter', 'mattress', 'protector', 'topper',
                    'wardrobe', 'closet', 'cabinet', 'dresser', 'nightstand',
                    'lamp', 'light', 'bulb', 'fixture', 'chandelier', 'sconce',
                    'picture frame', 'wall art', 'poster', 'canvas', 'decoration',
                    'vase', 'plant', 'pot', 'planter', 'watering', 'garden',
                    'doormat', 'rug', 'carpet', 'floor', 'tiles', 'wood',
                    'lock', 'handle', 'knob', 'hinge', 'door', 'stopper',
                    'clock', 'alarm', 'calendar', 'thermometer', 'humidity',
                    'fan', 'heater', 'humidifier', 'dehumidifier', 'purifier',
                    'iron', 'ironing board', 'steamer', 'clothes', 'drying',
                    'hangers', 'clips', 'pegs', 'rope', 'line',
                    # Cleaning expanded
                    'mop', 'broom', 'dustpan', 'bucket', 'spray', 'bottle',
                    'brush', 'duster', 'wipes', 'towel', 'rag', 'microfiber',
                    'squeegee', 'window cleaner', 'glass', 'polish', 'wax',
                    'disinfectant', 'sanitizer', 'detergent', 'bleach', 'fabric',
                    'toilet brush', 'plunger', 'scrub', 'grout', 'tile',
                    'gloves', 'rubber', 'protective', 'mask', 'safety',
                    # Bathroom expanded
                    'shower', 'bath', 'tub', 'curtain', 'liner', 'hooks',
                    'towel rack', 'bar', 'ring', 'tissue', 'paper', 'holder',
                    'soap dish', 'dispenser', 'toothbrush', 'holder', 'cup',
                    'mirror', 'cabinet', 'shelf', 'organizer', 'caddy', 'basket',
                    'mat', 'rug', 'non-slip', 'suction', 'adhesive',
                    'drain cover', 'hair catcher', 'filter', 'strainer',
                    'shampoo', 'conditioner', 'body wash', 'lotion', 'cream',
                    'razor', 'shaving', 'trimmer', 'scissors', 'nail',
                    'scale', 'weighing', 'digital', 'analog', 'mechanical',
                    # Car expanded
                    'sunshade', 'visor', 'windshield', 'window', 'tint',
                    'seat cover', 'cushion', 'lumbar', 'neck', 'pillow',
                    'steering wheel', 'grip', 'wrap', 'leather', 'cover',
                    'phone mount', 'holder', 'magnetic', 'suction', 'clip',
                    'charger', 'usb', 'adapter', 'cigarette', 'lighter', 'socket',
                    'air freshener', 'perfume', 'diffuser', 'vent', 'clip',
                    'organizer', 'trunk', 'backseat', 'storage', 'net', 'bag',
                    'trash bin', 'garbage', 'waste', 'bucket', 'container',
                    'cleaning', 'wash', 'sponge', 'cloth', 'towel', 'chamois',
                    'wax', 'polish', 'shine', 'tire', 'wheel', 'rim',
                    'dash cam', 'camera', 'recorder', 'dvr', 'parking',
                    'sensor', 'radar', 'detector', 'alarm', 'security',
                    'floor mat', 'carpet', 'rubber', 'weather', 'proof',
                    'sun visor', 'cd holder', 'tissue box', 'coin holder'],
        'exclude_keywords': ['fake', 'used', 'broken']
    },
    'beauty': {
        'channel_id': '@MissRedExpress',
        'name': 'Beauty & Fashion',
        'active': True,
        'posting_interval': 210,  # minutes (~3h 30m) - Specialized channel
        'min_price': 2,
        'max_price': 100,
        'min_commission': 5,
        'keywords': ['makeup', 'beauty', 'cosmetic', 'skincare', 'lipstick', 'eyeshadow',
                    'foundation', 'perfume', 'nail', 'jewelry', 'necklace', 'earring',
                    'bracelet', 'ring', 'fashion', 'accessory', 'bag', 'scarf', 'hair',
                    'brush', 'mirror', 'women', 'girl', 'lady', 'elegant', 'style',
                    # Makeup expanded
                    'mascara', 'eyeliner', 'eyebrow', 'brow', 'pencil', 'gel',
                    'blush', 'bronzer', 'highlighter', 'contour', 'palette',
                    'primer', 'concealer', 'powder', 'setting', 'finishing',
                    'lip gloss', 'lip liner', 'lip stain', 'lip balm', 'tint',
                    'lashes', 'false lashes', 'eyelash', 'curler', 'glue',
                    'makeup remover', 'cleansing', 'wipes', 'micellar', 'oil',
                    'sponge', 'beauty blender', 'applicator', 'puff', 'brush set',
                    'makeup bag', 'organizer', 'case', 'storage', 'travel',
                    # Skincare expanded
                    'cleanser', 'face wash', 'foam', 'gel', 'cream', 'oil',
                    'toner', 'essence', 'serum', 'ampoule', 'treatment',
                    'moisturizer', 'lotion', 'emulsion', 'day cream', 'night cream',
                    'eye cream', 'eye mask', 'patch', 'under eye', 'dark circle',
                    'face mask', 'sheet mask', 'clay mask', 'peel off', 'wash off',
                    'exfoliator', 'scrub', 'peeling', 'aha', 'bha', 'enzyme',
                    'sunscreen', 'spf', 'sun protection', 'uv', 'pa',
                    'vitamin c', 'retinol', 'hyaluronic', 'niacinamide', 'peptide',
                    'acne', 'pimple', 'blemish', 'spot', 'treatment',
                    'anti-aging', 'wrinkle', 'firming', 'lifting', 'tightening',
                    'whitening', 'brightening', 'glow', 'radiant', 'luminous',
                    'pore', 'minimizer', 'refining', 'blackhead', 'nose strip',
                    # Hair care
                    'shampoo', 'conditioner', 'hair mask', 'treatment', 'oil',
                    'hair spray', 'gel', 'wax', 'mousse', 'styling',
                    'hair dryer', 'blow dryer', 'straightener', 'curler', 'iron',
                    'comb', 'hairbrush', 'detangler', 'wide tooth', 'paddle',
                    'hair tie', 'elastic', 'scrunchie', 'headband', 'clip',
                    'hair pins', 'bobby pins', 'barrette', 'hairpin', 'accessories',
                    'hair color', 'dye', 'bleach', 'toner', 'developer',
                    'hair extensions', 'wig', 'toupee', 'hairpiece', 'clip-in',
                    # Nail care
                    'nail polish', 'lacquer', 'varnish', 'gel', 'shellac',
                    'nail art', 'stickers', 'decals', 'rhinestones', 'gems',
                    'nail file', 'buffer', 'clipper', 'cutter', 'trimmer',
                    'cuticle', 'pusher', 'nipper', 'oil', 'cream',
                    'base coat', 'top coat', 'primer', 'sealer', 'finish',
                    'nail remover', 'acetone', 'polish remover', 'wipes',
                    'manicure', 'pedicure', 'kit', 'set', 'tools',
                    'artificial nails', 'fake nails', 'press on', 'acrylic', 'tips',
                    # Jewelry expanded
                    'pendant', 'chain', 'choker', 'collar', 'locket',
                    'stud', 'hoop', 'dangle', 'drop', 'chandelier',
                    'bangle', 'cuff', 'charm', 'anklet', 'ankle bracelet',
                    'engagement', 'wedding', 'band', 'promise', 'eternity',
                    'birthstone', 'crystal', 'diamond', 'pearl', 'gemstone',
                    'gold', 'silver', 'rose gold', 'platinum', 'stainless steel',
                    'jewelry box', 'organizer', 'stand', 'holder', 'display',
                    'watch', 'smartwatch', 'bracelet', 'band', 'strap',
                    # Fashion accessories
                    'handbag', 'purse', 'clutch', 'tote', 'shoulder bag',
                    'crossbody', 'messenger', 'backpack', 'satchel', 'hobo',
                    'wallet', 'coin purse', 'cardholder', 'money clip', 'pouch',
                    'belt', 'waist', 'leather', 'buckle', 'chain',
                    'sunglasses', 'eyeglasses', 'glasses', 'frames', 'shades',
                    'hat', 'cap', 'beanie', 'beret', 'fedora', 'panama',
                    'scarf', 'shawl', 'wrap', 'stole', 'pashmina', 'bandana',
                    'gloves', 'mittens', 'fingerless', 'winter', 'leather',
                    'socks', 'stockings', 'tights', 'leggings', 'pantyhose',
                    # Perfume & fragrance
                    'perfume', 'cologne', 'fragrance', 'eau de parfum', 'edp',
                    'eau de toilette', 'body spray', 'mist', 'deodorant',
                    'essential oil', 'aromatherapy', 'diffuser', 'roller',
                    # Body care
                    'body lotion', 'body cream', 'body butter', 'moisturizer',
                    'body scrub', 'exfoliator', 'body polish', 'salt scrub',
                    'body wash', 'shower gel', 'soap', 'bath', 'bubble',
                    'hand cream', 'hand lotion', 'cuticle cream', 'nail care',
                    'foot cream', 'foot mask', 'heel balm', 'callus remover',
                    'massage oil', 'body oil', 'dry oil', 'shimmer'],
        'exclude_keywords': ['fake', 'men', 'boy', 'replica']
    },
    'under10': {
        'channel_id': '@AliUnder10Deals',
        'name': 'Under $10 Deals',
        'active': True,
        'posting_interval': 130,  # minutes (~2h 10m) - Fast channel
        'min_price': 0,  # Don't filter min in API, filter in code instead
        'max_price': 10,
        'min_commission': 2,
        # Use generic popular keywords to get results, then filter by price
        'keywords': ['phone', 'case', 'cable', 'holder', 'jewelry', 'ring', 'bracelet',
                    'earring', 'bag', 'wallet', 'key', 'toy', 'tool', 'led', 'sticker',
                    'nail', 'makeup', 'brush', 'pen', 'notebook', 'clip', 'hook',
                    # Phone accessories
                    'phone case', 'cover', 'silicone', 'tpu', 'bumper', 'clear',
                    'tempered glass', 'screen protector', 'film', 'guard',
                    'usb cable', 'charging', 'charger', 'adapter', 'plug',
                    'car holder', 'mount', 'stand', 'grip', 'ring holder',
                    'earphones', 'earbuds', 'headphones', 'aux', 'jack',
                    'selfie stick', 'tripod', 'remote', 'shutter', 'bluetooth',
                    # Jewelry & accessories
                    'necklace', 'pendant', 'chain', 'choker', 'locket',
                    'earrings', 'studs', 'hoops', 'dangle', 'drop',
                    'bracelet', 'bangle', 'cuff', 'anklet', 'charm',
                    'rings', 'band', 'adjustable', 'midi', 'knuckle',
                    'brooch', 'pin', 'badge', 'button', 'patch',
                    'hair accessories', 'hair tie', 'scrunchie', 'clip', 'pin',
                    'headband', 'elastic', 'bow', 'ribbon', 'flower',
                    # Fashion accessories
                    'sunglasses', 'glasses', 'shades', 'frames', 'retro',
                    'watch', 'wristwatch', 'digital', 'analog', 'strap',
                    'belt', 'waist belt', 'elastic belt', 'buckle', 'chain',
                    'socks', 'ankle socks', 'crew', 'no show', 'cotton',
                    'gloves', 'mittens', 'winter', 'fingerless', 'touchscreen',
                    'hat', 'cap', 'beanie', 'snapback', 'baseball',
                    'scarf', 'bandana', 'headscarf', 'neck warmer', 'infinity',
                    # Bags & wallets
                    'coin purse', 'small wallet', 'cardholder', 'card case', 'pouch',
                    'keychain', 'key ring', 'key holder', 'key organizer', 'carabiner',
                    'tote bag', 'shopping bag', 'canvas', 'reusable', 'foldable',
                    'makeup bag', 'cosmetic bag', 'travel pouch', 'organizer', 'zipper',
                    # Beauty & personal care
                    'lipstick', 'lip gloss', 'lip balm', 'lip tint', 'lip liner',
                    'eyeliner', 'mascara', 'eyebrow pencil', 'brow gel', 'lashes',
                    'makeup sponge', 'beauty blender', 'puff', 'applicator', 'brush',
                    'nail polish', 'nail art', 'stickers', 'decals', 'gems',
                    'nail file', 'buffer', 'clipper', 'cuticle pusher', 'tweezers',
                    'face mask', 'sheet mask', 'eye mask', 'nose strip', 'patch',
                    'hair clip', 'claw clip', 'bobby pins', 'barrette', 'hairpin',
                    'shower cap', 'bath sponge', 'loofah', 'body scrubber', 'pumice',
                    'razor', 'shaver', 'trimmer', 'eyebrow razor', 'facial razor',
                    # Home & kitchen
                    'sponge', 'scrubber', 'dish cloth', 'cleaning cloth', 'wipes',
                    'clips', 'clothespins', 'pegs', 'binder clips', 'paper clips',
                    'hooks', 'adhesive hooks', 'wall hooks', 'suction hooks', 'hangers',
                    'bag clips', 'seal clips', 'food clips', 'chip clips', 'sealer',
                    'coaster', 'drink coaster', 'mat', 'placemat', 'table mat',
                    'bottle opener', 'can opener', 'jar opener', 'lid opener', 'cork',
                    'straw', 'reusable straw', 'silicone straw', 'metal straw', 'brush',
                    'ice cube tray', 'mold', 'popsicle', 'ice maker', 'frozen',
                    'tea infuser', 'strainer', 'filter', 'ball', 'mesh',
                    'measuring spoon', 'cup', 'scoop', 'funnel', 'dropper',
                    # Stationery & office
                    'pen', 'ballpoint', 'gel pen', 'marker', 'highlighter',
                    'pencil', 'mechanical pencil', 'lead', 'eraser', 'sharpener',
                    'notebook', 'notepad', 'sticky notes', 'memo', 'post-it',
                    'bookmark', 'page marker', 'ruler', 'tape', 'glue',
                    'scissors', 'cutter', 'stapler', 'staples', 'remover',
                    # Electronics
                    'led light', 'keychain light', 'mini light', 'flashlight', 'torch',
                    'usb', 'otg', 'adapter', 'converter', 'splitter',
                    'cable organizer', 'cord holder', 'wire manager', 'clips', 'ties',
                    'battery', 'aaa', 'aa', 'button cell', 'coin battery',
                    # Toys & entertainment
                    'fidget', 'spinner', 'cube', 'toy', 'stress relief',
                    'puzzle', 'brain teaser', 'game', 'cards', 'dice',
                    'balloon', 'party', 'decoration', 'banner', 'confetti',
                    'stickers', 'decals', 'tattoo', 'temporary', 'transfer',
                    # Tools & hardware
                    'screwdriver', 'bit', 'allen key', 'hex', 'wrench',
                    'tape measure', 'ruler', 'level', 'laser', 'pointer',
                    'magnet', 'magnetic', 'strip', 'hook', 'holder',
                    # Pet accessories
                    'pet toy', 'cat toy', 'dog toy', 'ball', 'feather',
                    'collar', 'leash', 'harness', 'tag', 'id',
                    'bowl', 'feeder', 'water', 'food', 'dish'],
        'exclude_keywords': ['fake', 'replica', 'broken', 'used']
    },
    'under5': {
        'channel_id': '@AliUnder5Deals',
        'name': 'Under $5 Deals',
        'active': True,
        'posting_interval': 110,  # minutes (~1h 50m) - Fast channel
        'min_price': 0,  # Don't filter min in API, filter in code instead
        'max_price': 5,
        'min_commission': 1,
        # Use small/cheap item keywords
        'keywords': ['sticker', 'ring', 'earring', 'bracelet', 'nail', 'clip', 'hook',
                    'keychain', 'charm', 'button', 'patch', 'tape', 'pen', 'eraser',
                    'bookmark', 'magnet', 'badge', 'pin', 'cable tie', 'led',
                    # Jewelry & accessories (cheap)
                    'earrings', 'studs', 'small ring', 'toe ring', 'midi ring',
                    'anklet', 'ankle bracelet', 'friendship bracelet', 'string bracelet',
                    'brooch', 'safety pin', 'decorative pin', 'enamel pin',
                    'hair elastic', 'hair tie', 'rubber band', 'scrunchie mini',
                    'bobby pin', 'hair pin', 'clip small', 'mini barrette',
                    # Stickers & decals
                    'sticker pack', 'vinyl sticker', 'waterproof sticker', 'laptop sticker',
                    'phone sticker', 'nail sticker', 'nail decal', 'nail art',
                    'wall sticker', 'car sticker', 'emoji sticker', 'cute sticker',
                    'temporary tattoo', 'transfer', 'body sticker', 'face sticker',
                    # Keychains & charms
                    'key ring', 'key holder', 'key tag', 'key label',
                    'mini keychain', 'cute keychain', 'animal keychain', 'cartoon',
                    'charm', 'pendant charm', 'bag charm', 'zipper pull',
                    'phone charm', 'dust plug', 'jack plug', 'earphone plug',
                    # Nail care
                    'nail file', 'emery board', 'buffer', 'mini buffer',
                    'cuticle pusher', 'cuticle stick', 'orange stick', 'wood stick',
                    'nail sticker', 'nail gem', 'rhinestone', 'nail decoration',
                    'toe separator', 'nail spacer', 'pedicure tool', 'toe spreader',
                    # Beauty samples & minis
                    'lip balm', 'lip gloss mini', 'sample', 'travel size',
                    'makeup sample', 'perfume sample', 'tester', 'mini bottle',
                    'cotton pad', 'cotton swab', 'q-tip', 'makeup remover pad',
                    'blotting paper', 'oil control', 'face paper', 'tissue',
                    'eyebrow razor', 'facial razor', 'mini razor', 'shaver',
                    'makeup sponge', 'mini sponge', 'puff', 'small applicator',
                    # Hair accessories (cheap)
                    'hair band', 'headband thin', 'elastic band', 'ponytail holder',
                    'mini clip', 'claw clip mini', 'butterfly clip', 'snap clip',
                    'hair ribbon', 'bow', 'mini bow', 'hair bow',
                    # Office & stationery (cheap)
                    'ballpoint pen', 'gel pen', 'pencil', 'mini pencil',
                    'eraser', 'rubber', 'pencil eraser', 'mini eraser',
                    'sharpener', 'pencil sharpener', 'double hole', 'single',
                    'paper clip', 'metal clip', 'colored clip', 'mini clip',
                    'binder clip', 'mini binder', 'small clip', 'foldback',
                    'pushpin', 'thumbtack', 'drawing pin', 'bulletin board',
                    'sticky note', 'post-it small', 'memo pad', 'mini notepad',
                    'bookmark', 'page clip', 'page marker', 'book mark',
                    'rubber band', 'elastic band', 'hair tie', 'office band',
                    # Small tools & hardware
                    'cable tie', 'zip tie', 'wire tie', 'plastic tie',
                    'cable clip', 'cord organizer', 'wire clip', 'adhesive clip',
                    'suction cup', 'hook small', 'mini hook', 'adhesive hook',
                    'magnet', 'mini magnet', 'fridge magnet', 'magnetic strip',
                    'velcro', 'hook loop', 'adhesive velcro', 'sticky back',
                    'safety pin', 'diaper pin', 'sewing pin', 'straight pin',
                    'needle', 'sewing needle', 'hand needle', 'embroidery',
                    'thread', 'sewing thread', 'cotton thread', 'polyester',
                    'button', 'snap button', 'press stud', 'fastener',
                    # Electronics accessories (cheap)
                    'cable protector', 'cord saver', 'cable cover', 'spring',
                    'earphone holder', 'cord wrap', 'cable winder', 'organizer',
                    'dust plug', 'port cover', 'phone plug', 'dust cap',
                    'sim card', 'adapter', 'sim tool', 'ejector pin',
                    'screen wipe', 'cleaning cloth', 'microfiber small', 'lens cloth',
                    # Home & kitchen (cheap)
                    'bag clip', 'food clip', 'seal clip', 'chip clip',
                    'clothespin', 'peg', 'clothes peg', 'hanging clip',
                    'sponge', 'mini sponge', 'scrubber small', 'dish sponge',
                    'drain cover', 'sink strainer', 'filter', 'hair catcher',
                    'soap dish', 'soap holder', 'travel soap', 'soap case',
                    'ice cube tray', 'mini tray', 'small mold', 'ice mold',
                    'toothpick', 'dental pick', 'floss pick', 'oral care',
                    'straw', 'mini straw', 'cocktail straw', 'short straw',
                    # Craft & DIY
                    'beads', 'craft bead', 'plastic bead', 'glass bead',
                    'sequin', 'glitter', 'craft supply', 'decoration',
                    'ribbon', 'craft ribbon', 'satin ribbon', 'grosgrain',
                    'lace', 'trim', 'fabric trim', 'decorative trim',
                    'felt', 'craft felt', 'fabric square', 'diy material',
                    # Travel & portable
                    'pill box', 'pill case', 'medicine box', 'vitamin case',
                    'contact lens case', 'lens holder', 'travel case', 'mini case',
                    'mini bottle', 'travel bottle', 'small container', 'sample jar',
                    'luggage tag', 'bag tag', 'id tag', 'name tag',
                    # Party & celebration
                    'balloon', 'mini balloon', 'party balloon', 'latex balloon',
                    'candle', 'birthday candle', 'cake candle', 'party candle',
                    'confetti', 'party confetti', 'table confetti', 'sprinkle',
                    'party favor', 'goodie bag', 'gift bag small', 'treat bag',
                    # Miscellaneous
                    'mirror', 'mini mirror', 'pocket mirror', 'compact mirror',
                    'comb', 'mini comb', 'pocket comb', 'folding comb',
                    'whistle', 'mini whistle', 'keychain whistle', 'sport whistle',
                    'dice', 'game dice', 'd6', 'small dice'],
        'exclude_keywords': ['fake', 'replica', 'broken', 'used']
    }
}

# Global bot settings
BOT_SETTINGS = {
    'active': True
}

# Track posted products to avoid duplicates
POSTED_PRODUCTS = set()  # Store product IDs
MAX_POSTED_HISTORY = 1000  # Maximum products to remember

class AliExpressAPI:
    """Handler for AliExpress Affiliates API"""
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.api_url = ALIEXPRESS_API_URL
    
    def _generate_sign(self, params: Dict[str, str]) -> str:
        """Generate signature for AliExpress API request"""
        # Sort all parameters alphabetically
        sorted_params = sorted(params.items())
        
        # Create signature string: just sorted key-value pairs (no API path)
        sign_string = ''
        for key, value in sorted_params:
            sign_string += str(key) + str(value)
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature
    
    def get_hot_products(self, page_size: int = 50, channel_config: Dict = None, category_ids: Optional[str] = None, retry_without_keywords: bool = True) -> List[Dict]:
        """Fetch hot products from AliExpress with channel-specific filtering"""
        logger.info("Fetching hot products from AliExpress...")
        
        # Check if bot is active
        if not BOT_SETTINGS['active']:
            logger.info("Bot is paused by admin")
            return []
        
        # Use default config if none provided
        if channel_config is None:
            channel_config = CHANNELS_CONFIG.get('hot_deals', list(CHANNELS_CONFIG.values())[0])
        
        # Build parameters
        params = {
            'app_key': self.app_key,
            'format': 'json',
            'method': 'aliexpress.affiliate.product.query',
            'sign_method': 'sha256',
            'timestamp': str(int(time.time() * 1000)),
            'v': '2.0',
        }
        
        # Add API specific parameters
        api_params = {
            'page_no': '1',
            'page_size': str(page_size),
            'target_currency': 'USD',
            'target_language': 'EN',
            'sort': 'LAST_VOLUME_DESC',
            'tracking_id': 'Safar100',
        }
        
        # Add category_ids if provided
        if category_ids:
            api_params['category_ids'] = category_ids
            
        # Add price range from channel config
        # Note: AliExpress API doesn't support decimal min_price, so only add if >= 1
        min_price = channel_config.get('min_price', 0)
        if min_price >= 1:
            api_params['min_sale_price'] = str(int(min_price))
        
        # Max price is always sent
        if channel_config.get('max_price', 10000) < 10000:
            api_params['max_sale_price'] = str(int(channel_config['max_price']))
            
        # Add keywords from channel config with rotation
        keywords = channel_config.get('keywords', [])
        if keywords:
            # Randomly select 3-5 keywords for variety (instead of always first 3)
            import random
            num_keywords = min(random.randint(3, 5), len(keywords))
            selected_keywords = random.sample(keywords, num_keywords)
            api_params['keywords'] = ','.join(selected_keywords)
            logger.info(f"Using keywords: {', '.join(selected_keywords)}")
        
        # Merge all parameters for signature
        all_params = {**params, **api_params}
        
        # Generate signature
        sign = self._generate_sign(all_params)
        params['sign'] = sign
        
        # Add API params to request params
        params.update(api_params)
        
        logger.info(f"Requesting AliExpress API: /{params['method']}")
        
        try:
            response = requests.get(self.api_url, params=params, timeout=60)
            data = response.json()
            
            if 'error_response' in data:
                error = data['error_response']
                logger.error(f"API Error: {error.get('code')} - {error.get('msg')}")
                return []
            
            if 'aliexpress_affiliate_product_query_response' in data:
                resp_result = data['aliexpress_affiliate_product_query_response'].get('resp_result')
                
                if resp_result and resp_result.get('resp_code') == 200:
                    result = resp_result.get('result', {})
                    products_data = result.get('products', {})
                    
                    if products_data:
                        if isinstance(products_data, dict):
                            products = products_data.get('product', [])
                        else:
                            products = products_data
                        
                        if products:
                            # Ensure it's a list
                            if not isinstance(products, list):
                                products = [products]
                            
                            # Filter products with smart filtering
                            valid_products = []
                            for product in products:
                                # Check if product has promotion link
                                if not product.get('promotion_link'):
                                    continue
                                
                                # Get product details
                                product_id = product.get('product_id')
                                title = product.get('product_title', '').lower()
                                price = float(product.get('target_sale_price', 0))
                                original_price = float(product.get('target_original_price', price))
                                
                                # Parse commission rate (remove % sign if present)
                                commission_str = str(product.get('commission_rate', '0'))
                                commission_rate = float(commission_str.replace('%', '').strip())
                                
                                # 0. Check for real discount - skip products with no discount
                                if original_price <= price:
                                    logger.debug(f"Skipping product with no discount: {title[:50]}... (original=${original_price}, sale=${price})")
                                    continue
                                
                                # 1. Check for duplicates
                                if product_id in POSTED_PRODUCTS:
                                    logger.debug(f"Skipping duplicate product: {product_id}")
                                    continue
                                
                                # 2. Filter by price range
                                min_price = channel_config.get('min_price', 0)
                                max_price = channel_config.get('max_price', 10000)
                                if min_price > 0 and price < min_price:
                                    logger.debug(f"Product price ${price} below minimum ${min_price}")
                                    continue
                                if max_price < 10000 and price > max_price:
                                    logger.debug(f"Product price ${price} above maximum ${max_price}")
                                    continue
                                
                                # 3. Filter by commission rate
                                min_commission = channel_config.get('min_commission', 0)
                                if commission_rate < min_commission:
                                    logger.debug(f"Product commission {commission_rate}% below minimum {min_commission}%")
                                    continue
                                
                                # 4. Filter by keywords (include)
                                keywords = channel_config.get('keywords', [])
                                if keywords:
                                    has_keyword = False
                                    for keyword in keywords:
                                        if keyword.lower() in title:
                                            has_keyword = True
                                            break
                                    if not has_keyword:
                                        logger.debug(f"Product doesn't contain required keywords")
                                        continue
                                
                                # 5. Filter by exclude keywords
                                exclude_keywords = channel_config.get('exclude_keywords', [])
                                if exclude_keywords:
                                    has_exclude = False
                                    for keyword in exclude_keywords:
                                        if keyword.lower() in title:
                                            has_exclude = True
                                            logger.debug(f"Product contains excluded keyword: {keyword}")
                                            break
                                    if has_exclude:
                                        continue
                                
                                # Product passed all filters
                                valid_products.append(product)
                            
                            if valid_products:
                                logger.info(f"Successfully fetched {len(valid_products)} real products with tracking!")
                                logger.info(f"Filters applied: price(${channel_config.get('min_price', 0)}-${channel_config.get('max_price', 10000)}), commission({channel_config.get('min_commission', 0)}%), keywords({len(channel_config.get('keywords', []))}), exclude({len(channel_config.get('exclude_keywords', []))})")
                                return valid_products
            
            # Fallback: If no products found and we have keywords, try again without keywords
            if retry_without_keywords and channel_config.get('keywords'):
                logger.warning("No products found with keywords, retrying without keywords...")
                # Create a copy without keywords
                fallback_config = channel_config.copy()
                fallback_config['keywords'] = []
                return self.get_hot_products(page_size=page_size, channel_config=fallback_config, 
                                            category_ids=category_ids, retry_without_keywords=False)
            
            logger.warning("No valid products with tracking found - skipping this cycle")
            return []
            
        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            logger.info("Skipping this cycle - no real products available")
            return []
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            logger.info("Skipping this cycle - no real products available")
            return []

class TelegramPoster:
    """Handler for posting to Telegram channel"""
    
    def __init__(self, bot_token: str, channel_id: str):
        self.bot = Bot(token=bot_token)
        self.channel_id = channel_id
    
    def shorten_url(self, long_url: str) -> str:
        """Shorten URL using TinyURL API"""
        try:
            response = requests.get(f'http://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}', timeout=5)
            if response.status_code == 200:
                short_url = response.text.strip()
                logger.info(f"URL shortened: {short_url}")
                return short_url
            else:
                logger.warning(f"Failed to shorten URL, using original")
                return long_url
        except Exception as e:
            logger.warning(f"Error shortening URL: {e}, using original")
            return long_url
    
    async def post_product(self, product: Dict) -> bool:
        """Post a single product to the Telegram channel"""
        try:
            # Extract product information
            product_id = product.get('product_id')
            title = product.get('product_title', 'منتج رائع')
            price = product.get('target_sale_price', '0')
            original_price = product.get('target_original_price', price)
            commission_rate = product.get('commission_rate', '0')
            image_url = product.get('product_main_image_url', '')
            promotion_link = product.get('promotion_link', '')
            
            # Shorten the URL for cleaner links
            short_link = self.shorten_url(promotion_link)
            
            # Check if already posted (double-check)
            if product_id in POSTED_PRODUCTS:
                logger.warning(f"Product {product_id} already posted, skipping")
                return False
            
            # Calculate discount
            try:
                discount = int(((float(original_price) - float(price)) / float(original_price)) * 100)
            except (ValueError, ZeroDivisionError):
                discount = 0
            
            # Create inline keyboard with buy button (using short link)
            keyboard = [[InlineKeyboardButton("🛒 Buy Now", url=short_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Format product details
            caption = f"""🛍️ {title}

💰 Price: ${price} USD
💵 Original: ${original_price}
🔥 Save {discount}%!
⭐ Rating: {product.get('evaluate_rate', '0')}%

✨ Limited Time Offer!
⚡ Shop Now & Save Big!"""
            
            # Send message with image and details combined
            if image_url:
                await self.bot.send_photo(
                    chat_id=self.channel_id,
                    photo=image_url,
                    caption=caption,
                    reply_markup=reply_markup
                )
            else:
                # Send text only if no image
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=caption,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
            
            logger.info(f"Successfully posted product: {title[:50]}...")
            
            # Add product to posted history
            POSTED_PRODUCTS.add(product_id)
            
            # Manage history size - remove oldest if exceeds limit
            if len(POSTED_PRODUCTS) > MAX_POSTED_HISTORY:
                # Remove approximately 20% of oldest entries
                remove_count = int(MAX_POSTED_HISTORY * 0.2)
                for _ in range(remove_count):
                    POSTED_PRODUCTS.pop()
            
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error posting product: {e}")
            return False
        except Exception as e:
            logger.error(f"Error posting product: {e}")
            return False

async def post_products_job():
    """Post products job for all active channels"""
    try:
        logger.info("Starting scheduled product posting job for all channels...")
        
        # Initialize API handler
        aliexpress_api = AliExpressAPI(APP_KEY, APP_SECRET)
        
        # Process each channel
        for channel_key, channel_config in CHANNELS_CONFIG.items():
            if not channel_config.get('active', False):
                logger.info(f"Channel '{channel_config['name']}' is inactive, skipping")
                continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing channel: {channel_config['name']} ({channel_key})")
            logger.info(f"Channel ID: {channel_config['channel_id']}")
            
            # Get products with channel-specific filters (higher page_size = more variety)
            products = aliexpress_api.get_hot_products(page_size=50, channel_config=channel_config)
            
            if not products:
                logger.info(f"No products found for {channel_config['name']}, skipping")
                continue
            
            logger.info(f"Fetched {len(products)} products for {channel_config['name']}")
            
            # Initialize telegram poster for this channel
            telegram = TelegramPoster(TELEGRAM_BOT_TOKEN, channel_config['channel_id'])
            
            # Randomly select products to post (more for Hot Finds, less for others)
            if channel_key == 'hot_deals':
                # Hot Finds: post 3-6 products for variety
                num_to_post = random.randint(3, min(6, len(products)))
            else:
                # Other channels: 1-3 products
                num_to_post = random.randint(1, min(3, len(products)))
            
            selected_products = random.sample(products, num_to_post)
            
            posted_count = 0
            for product in selected_products:
                if await telegram.post_product(product):
                    posted_count += 1
                    # Random delay between posts (3-8 seconds) - more human-like
                    delay = random.randint(3, 8)
                    await asyncio.sleep(delay)
            
            logger.info(f"Posted {posted_count}/{num_to_post} products to {channel_config['name']}")
            
            # Random delay between channels (8-15 seconds) - more natural
            channel_delay = random.randint(8, 15)
            await asyncio.sleep(channel_delay)
        
        logger.info(f"\n{'='*60}")
        logger.info("Completed posting job for all channels")
        
    except Exception as e:
        logger.error(f"Error in posting job: {e}")

async def handle_admin_commands():
    """Handle admin commands with inline keyboard control panel"""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    last_update_id = 0
    
    while True:
        try:
            updates = await bot.get_updates(offset=last_update_id + 1, timeout=5)
            
            for update in updates:
                last_update_id = update.update_id
                
                # Handle callback queries (button clicks)
                if update.callback_query:
                    query = update.callback_query
                    if query.from_user.id not in ADMIN_USER_IDS:
                        continue
                    
                    callback_data = query.data
                    chat_id = query.message.chat_id
                    message_id = query.message.message_id
                    
                    # Global controls
                    if callback_data == 'main_menu':
                        keyboard = [
                            [InlineKeyboardButton("📺 التحكم بالقنوات", callback_data='channels_menu')],
                            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats'),
                             InlineKeyboardButton("🧪 اختبار فوري", callback_data='test')],
                            [InlineKeyboardButton("🔴 إيقاف البوت" if BOT_SETTINGS['active'] else "🟢 تشغيل البوت", callback_data='toggle_bot')],
                            [InlineKeyboardButton("🔄 مسح السجل", callback_data='reset_duplicates')]
                        ]
                        status = "🟢 يعمل" if BOT_SETTINGS['active'] else "🔴 متوقف"
                        message = f"""🎛️ **لوحة التحكم الرئيسية**

📊 **الحالة:** {status}
📦 **منتجات منشورة:** {len(POSTED_PRODUCTS)}

👇 اختر من القائمة:"""
                        await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data == 'toggle_bot':
                        BOT_SETTINGS['active'] = not BOT_SETTINGS['active']
                        status_text = "تم تشغيل" if BOT_SETTINGS['active'] else "تم إيقاف"
                        await query.answer(f"{status_text} البوت!")
                        # Refresh main menu
                        keyboard = [
                            [InlineKeyboardButton("📺 التحكم بالقنوات", callback_data='channels_menu')],
                            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats'),
                             InlineKeyboardButton("🧪 اختبار فوري", callback_data='test')],
                            [InlineKeyboardButton("🔴 إيقاف البوت" if BOT_SETTINGS['active'] else "🟢 تشغيل البوت", callback_data='toggle_bot')],
                            [InlineKeyboardButton("🔄 مسح السجل", callback_data='reset_duplicates')]
                        ]
                        status = "🟢 يعمل" if BOT_SETTINGS['active'] else "🔴 متوقف"
                        message = f"""🎛️ **لوحة التحكم الرئيسية**

📊 **الحالة:** {status}
📦 **منتجات منشورة:** {len(POSTED_PRODUCTS)}

👇 اختر من القائمة:"""
                        await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data == 'test':
                        await query.answer("🧪 جاري اختبار...")
                        await post_products_job()
                        await bot.send_message(chat_id, "✅ تم الاختبار! تحقق من القنوات")
                    
                    elif callback_data == 'reset_duplicates':
                        count = len(POSTED_PRODUCTS)
                        POSTED_PRODUCTS.clear()
                        await query.answer(f"تم مسح {count} منتج")
                        await bot.send_message(chat_id, f"✅ تم مسح سجل {count} منتج")
                    
                    elif callback_data == 'stats':
                        status = "🟢 يعمل" if BOT_SETTINGS['active'] else "🔴 متوقف"
                        active_channels = sum(1 for c in CHANNELS_CONFIG.values() if c.get('active', False))
                        total_keywords = sum(len(c.get('keywords', [])) for c in CHANNELS_CONFIG.values())
                        
                        message = f"""📊 **إحصائيات البوت**

🔹 **الحالة العامة:** {status}
🔹 **القنوات النشطة:** {active_channels}/6
🔹 **منتجات منشورة:** {len(POSTED_PRODUCTS)}
🔹 **إجمالي الكلمات:** {total_keywords}

📺 **تفاصيل القنوات:**"""
                        
                        for key, config in CHANNELS_CONFIG.items():
                            emoji = "✅" if config.get('active', False) else "❌"
                            message += f"\n{emoji} {config['name']}: {config['posting_interval']}دق"
                        
                        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='main_menu')]]
                        await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data == 'channels_menu':
                        message = "📺 **التحكم بالقنوات**\n\nاختر قناة للتحكم بها:"
                        keyboard = []
                        for key, config in CHANNELS_CONFIG.items():
                            emoji = "✅" if config.get('active', False) else "❌"
                            keyboard.append([InlineKeyboardButton(f"{emoji} {config['name']}", callback_data=f'channel_{key}')])
                        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='main_menu')])
                        await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    # Channel-specific controls
                    elif callback_data.startswith('channel_'):
                        channel_key = callback_data.replace('channel_', '')
                        if channel_key in CHANNELS_CONFIG:
                            config = CHANNELS_CONFIG[channel_key]
                            active = config.get('active', False)
                            
                            message = f"""⚙️ **{config['name']}**

📊 **الإعدادات الحالية:**
• الحالة: {'✅ نشط' if active else '❌ متوقف'}
• معرف القناة: `{config['channel_id']}`
• التوقيت: كل {config['posting_interval']} دقيقة
• السعر: ${config['min_price']} - ${config['max_price']}
• العمولة: {config['min_commission']}%+
• كلمات مفتاحية: {len(config.get('keywords', []))}

👇 اختر إجراء:"""
                            
                            keyboard = [
                                [InlineKeyboardButton("🔴 تعطيل" if active else "🟢 تفعيل", callback_data=f'toggle_{channel_key}')],
                                [InlineKeyboardButton("⏱️ تغيير الوقت", callback_data=f'time_{channel_key}'),
                                 InlineKeyboardButton("🧪 اختبار", callback_data=f'test_{channel_key}')],
                            ]
                            # Add price control for channels except under5 and under10
                            if channel_key not in ['under5', 'under10']:
                                keyboard.append([InlineKeyboardButton("💰 تغيير السعر", callback_data=f'price_{channel_key}')])
                            keyboard.extend([
                                [InlineKeyboardButton("📊 معلومات الفلاتر", callback_data=f'filters_{channel_key}')],
                                [InlineKeyboardButton("🔙 قائمة القنوات", callback_data='channels_menu')]
                            ])
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data.startswith('toggle_'):
                        channel_key = callback_data.replace('toggle_', '')
                        if channel_key in CHANNELS_CONFIG:
                            CHANNELS_CONFIG[channel_key]['active'] = not CHANNELS_CONFIG[channel_key].get('active', False)
                            status = "تم تفعيل" if CHANNELS_CONFIG[channel_key]['active'] else "تم تعطيل"
                            await query.answer(f"{status} القناة!")
                            
                            # Refresh channel page
                            config = CHANNELS_CONFIG[channel_key]
                            active = config.get('active', False)
                            message = f"""⚙️ **{config['name']}**

📊 **الإعدادات الحالية:**
• الحالة: {'✅ نشط' if active else '❌ متوقف'}
• معرف القناة: `{config['channel_id']}`
• التوقيت: كل {config['posting_interval']} دقيقة
• السعر: ${config['min_price']} - ${config['max_price']}
• العمولة: {config['min_commission']}%+
• كلمات مفتاحية: {len(config.get('keywords', []))}

👇 اختر إجراء:"""
                            
                            keyboard = [
                                [InlineKeyboardButton("🔴 تعطيل" if active else "🟢 تفعيل", callback_data=f'toggle_{channel_key}')],
                                [InlineKeyboardButton("⏱️ تغيير الوقت", callback_data=f'time_{channel_key}'),
                                 InlineKeyboardButton("🧪 اختبار", callback_data=f'test_{channel_key}')],
                            ]
                            # Add price control for channels except under5 and under10
                            if channel_key not in ['under5', 'under10']:
                                keyboard.append([InlineKeyboardButton("💰 تغيير السعر", callback_data=f'price_{channel_key}')])
                            keyboard.extend([
                                [InlineKeyboardButton("📊 معلومات الفلاتر", callback_data=f'filters_{channel_key}')],
                                [InlineKeyboardButton("🔙 قائمة القنوات", callback_data='channels_menu')]
                            ])
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data.startswith('time_'):
                        channel_key = callback_data.replace('time_', '')
                        if channel_key in CHANNELS_CONFIG:
                            config = CHANNELS_CONFIG[channel_key]
                            current = config['posting_interval']
                            
                            message = f"""⏱️ **تغيير توقيت {config['name']}**

⏰ **التوقيت الحالي:** {current} دقيقة

👇 اختر توقيت جديد:"""
                            
                            keyboard = [
                                [InlineKeyboardButton("60 دقيقة (1 ساعة)", callback_data=f'settime_{channel_key}_60'),
                                 InlineKeyboardButton("90 دقيقة (1.5 ساعة)", callback_data=f'settime_{channel_key}_90')],
                                [InlineKeyboardButton("120 دقيقة (2 ساعة)", callback_data=f'settime_{channel_key}_120'),
                                 InlineKeyboardButton("150 دقيقة (2.5 ساعة)", callback_data=f'settime_{channel_key}_150')],
                                [InlineKeyboardButton("180 دقيقة (3 ساعات)", callback_data=f'settime_{channel_key}_180'),
                                 InlineKeyboardButton("210 دقيقة (3.5 ساعة)", callback_data=f'settime_{channel_key}_210')],
                                [InlineKeyboardButton("240 دقيقة (4 ساعات)", callback_data=f'settime_{channel_key}_240'),
                                 InlineKeyboardButton("300 دقيقة (5 ساعات)", callback_data=f'settime_{channel_key}_300')],
                                [InlineKeyboardButton("🔙 رجوع", callback_data=f'channel_{channel_key}')]
                            ]
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data.startswith('settime_'):
                        parts = callback_data.split('_')
                        channel_key = parts[1]
                        new_time = int(parts[2])
                        if channel_key in CHANNELS_CONFIG:
                            CHANNELS_CONFIG[channel_key]['posting_interval'] = new_time
                            await query.answer(f"✅ تم تغيير التوقيت إلى {new_time} دقيقة")
                            
                            # Back to channel page
                            config = CHANNELS_CONFIG[channel_key]
                            active = config.get('active', False)
                            message = f"""⚙️ **{config['name']}**

📊 **الإعدادات الحالية:**
• الحالة: {'✅ نشط' if active else '❌ متوقف'}
• معرف القناة: `{config['channel_id']}`
• التوقيت: كل {config['posting_interval']} دقيقة
• السعر: ${config['min_price']} - ${config['max_price']}
• العمولة: {config['min_commission']}%+
• كلمات مفتاحية: {len(config.get('keywords', []))}

👇 اختر إجراء:"""
                            
                            keyboard = [
                                [InlineKeyboardButton("🔴 تعطيل" if active else "🟢 تفعيل", callback_data=f'toggle_{channel_key}')],
                                [InlineKeyboardButton("⏱️ تغيير الوقت", callback_data=f'time_{channel_key}'),
                                 InlineKeyboardButton("🧪 اختبار", callback_data=f'test_{channel_key}')],
                            ]
                            # Add price control for channels except under5 and under10
                            if channel_key not in ['under5', 'under10']:
                                keyboard.append([InlineKeyboardButton("💰 تغيير السعر", callback_data=f'price_{channel_key}')])
                            keyboard.extend([
                                [InlineKeyboardButton("📊 معلومات الفلاتر", callback_data=f'filters_{channel_key}')],
                                [InlineKeyboardButton("🔙 قائمة القنوات", callback_data='channels_menu')]
                            ])
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data.startswith('test_'):
                        channel_key = callback_data.replace('test_', '')
                        await query.answer(f"🧪 جاري اختبار {CHANNELS_CONFIG[channel_key]['name']}...")
                        # Test this specific channel
                        if channel_key in CHANNELS_CONFIG:
                            original_active = CHANNELS_CONFIG[channel_key]['active']
                            CHANNELS_CONFIG[channel_key]['active'] = True
                            await post_products_job()
                            CHANNELS_CONFIG[channel_key]['active'] = original_active
                            await bot.send_message(chat_id, f"✅ تم اختبار {CHANNELS_CONFIG[channel_key]['name']}!")
                    
                    elif callback_data.startswith('price_'):
                        channel_key = callback_data.replace('price_', '')
                        if channel_key in CHANNELS_CONFIG and channel_key not in ['under5', 'under10']:
                            config = CHANNELS_CONFIG[channel_key]
                            current_min = config['min_price']
                            current_max = config['max_price']
                            
                            message = f"""💰 **تغيير نطاق السعر لـ {config['name']}**

💵 **النطاق الحالي:** ${current_min} - ${current_max}

👇 اختر نطاق سعر جديد:"""
                            
                            keyboard = [
                                [InlineKeyboardButton("$0 - $20", callback_data=f'setprice_{channel_key}_0_20'),
                                 InlineKeyboardButton("$0 - $50", callback_data=f'setprice_{channel_key}_0_50')],
                                [InlineKeyboardButton("$0 - $100", callback_data=f'setprice_{channel_key}_0_100'),
                                 InlineKeyboardButton("$0 - $150", callback_data=f'setprice_{channel_key}_0_150')],
                                [InlineKeyboardButton("$0 - $200", callback_data=f'setprice_{channel_key}_0_200'),
                                 InlineKeyboardButton("$0 - $300", callback_data=f'setprice_{channel_key}_0_300')],
                                [InlineKeyboardButton("$0 - $400", callback_data=f'setprice_{channel_key}_0_400'),
                                 InlineKeyboardButton("$0 - $500", callback_data=f'setprice_{channel_key}_0_500')],
                                [InlineKeyboardButton("$5 - $100", callback_data=f'setprice_{channel_key}_5_100'),
                                 InlineKeyboardButton("$10 - $200", callback_data=f'setprice_{channel_key}_10_200')],
                                [InlineKeyboardButton("$20 - $300", callback_data=f'setprice_{channel_key}_20_300'),
                                 InlineKeyboardButton("$50 - $500", callback_data=f'setprice_{channel_key}_50_500')],
                                [InlineKeyboardButton("🔙 رجوع", callback_data=f'channel_{channel_key}')]
                            ]
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data.startswith('setprice_'):
                        # Remove 'setprice_' prefix and split from the end to get prices
                        data = callback_data.replace('setprice_', '')
                        parts = data.rsplit('_', 2)  # Split from right to get last 2 parts (min, max)
                        channel_key = parts[0]
                        min_price = int(parts[1])
                        max_price = int(parts[2])
                        if channel_key in CHANNELS_CONFIG and channel_key not in ['under5', 'under10']:
                            CHANNELS_CONFIG[channel_key]['min_price'] = min_price
                            CHANNELS_CONFIG[channel_key]['max_price'] = max_price
                            await query.answer(f"✅ تم تغيير السعر إلى ${min_price}-${max_price}")
                            
                            # Back to channel page
                            config = CHANNELS_CONFIG[channel_key]
                            active = config.get('active', False)
                            message = f"""⚙️ **{config['name']}**

📊 **الإعدادات الحالية:**
• الحالة: {'✅ نشط' if active else '❌ متوقف'}
• معرف القناة: `{config['channel_id']}`
• التوقيت: كل {config['posting_interval']} دقيقة
• السعر: ${config['min_price']} - ${config['max_price']}
• العمولة: {config['min_commission']}%+
• كلمات مفتاحية: {len(config.get('keywords', []))}

👇 اختر إجراء:"""
                            
                            keyboard = [
                                [InlineKeyboardButton("🔴 تعطيل" if active else "🟢 تفعيل", callback_data=f'toggle_{channel_key}')],
                                [InlineKeyboardButton("⏱️ تغيير الوقت", callback_data=f'time_{channel_key}'),
                                 InlineKeyboardButton("🧪 اختبار", callback_data=f'test_{channel_key}')],
                            ]
                            # Add price control for channels except under5 and under10
                            if channel_key not in ['under5', 'under10']:
                                keyboard.append([InlineKeyboardButton("💰 تغيير السعر", callback_data=f'price_{channel_key}')])
                            keyboard.extend([
                                [InlineKeyboardButton("📊 معلومات الفلاتر", callback_data=f'filters_{channel_key}')],
                                [InlineKeyboardButton("🔙 قائمة القنوات", callback_data='channels_menu')]
                            ])
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                    
                    elif callback_data.startswith('filters_'):
                        channel_key = callback_data.replace('filters_', '')
                        if channel_key in CHANNELS_CONFIG:
                            config = CHANNELS_CONFIG[channel_key]
                            keywords = config.get('keywords', [])
                            exclude = config.get('exclude_keywords', [])
                            keywords_preview = ', '.join(keywords[:10]) + ('...' if len(keywords) > 10 else '') if keywords else 'لا يوجد'
                            exclude_preview = ', '.join(exclude) if exclude else 'لا يوجد'
                            
                            message = f"""🎯 **فلاتر {config['name']}**

💰 **السعر:**
• الحد الأدنى: ${config['min_price']}
• الحد الأقصى: ${config['max_price']}

💵 **العمولة:**
• الحد الأدنى: {config['min_commission']}%

🔑 **الكلمات المفتاحية:**
• العدد: {len(keywords)}
• أمثلة: {keywords_preview}

🚫 **كلمات الاستبعاد:**
• {exclude_preview}"""
                            
                            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f'channel_{channel_key}')]]
                            await bot.edit_message_text(message, chat_id, message_id, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                
                # Handle text messages
                if update.message and update.message.from_user.id in ADMIN_USER_IDS:
                    text = update.message.text
                    chat_id = update.message.chat_id
                    
                    if text == '/start' or text == '/menu':
                        keyboard = [
                            [InlineKeyboardButton("📺 التحكم بالقنوات", callback_data='channels_menu')],
                            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats'),
                             InlineKeyboardButton("🧪 اختبار فوري", callback_data='test')],
                            [InlineKeyboardButton("🔴 إيقاف البوت" if BOT_SETTINGS['active'] else "🟢 تشغيل البوت", callback_data='toggle_bot')],
                            [InlineKeyboardButton("🔄 مسح السجل", callback_data='reset_duplicates')]
                        ]
                        status = "🟢 يعمل" if BOT_SETTINGS['active'] else "🔴 متوقف"
                        message = f"""🎛️ **لوحة التحكم الرئيسية**

📊 **الحالة:** {status}
📦 **منتجات منشورة:** {len(POSTED_PRODUCTS)}

👇 اختر من القائمة:"""
                        await bot.send_message(chat_id, message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
        except Exception as e:
            # Ignore "message not modified" errors - they're not critical
            if "Message is not modified" not in str(e):
                logger.error(f"Error handling admin commands: {e}")
            await asyncio.sleep(1)

async def periodic_poster():
    """Run periodic product posting with randomized intervals"""
    # Random initial wait (20-60 seconds) - more natural
    initial_wait = random.randint(20, 60)
    logger.info(f"Waiting {initial_wait} seconds before first post...")
    await asyncio.sleep(initial_wait)
    
    while True:
        if BOT_SETTINGS['active']:
            await post_products_job()
        
        # Get minimum interval and add randomization (±5 minutes)
        min_interval = min([config['posting_interval'] for config in CHANNELS_CONFIG.values() if config.get('active', False)], default=30)
        
        # Add random variation: -5 to +5 minutes
        random_variation = random.randint(-5, 5)
        actual_interval = max(15, min_interval + random_variation)  # Never less than 15 minutes
        
        logger.info(f"Next post cycle in {actual_interval} minutes (base: {min_interval} min)")
        await asyncio.sleep(actual_interval * 60)

async def main():
    """Main function to run the bot"""
    logger.info("=== AliExpress Multi-Channel Bot Started ===")
    logger.info("\nActive Channels:")
    for key, config in CHANNELS_CONFIG.items():
        if config.get('active', False):
            logger.info(f"  - {config['name']}: {config['channel_id']} (every {config['posting_interval']} min)")
            logger.info(f"    Filters: ${config['min_price']}-${config['max_price']}, {len(config['keywords'])} keywords")
    logger.info(f"\nAdmin IDs: {', '.join(map(str, ADMIN_USER_IDS))}")
    logger.info("Features: Multi-channel + Smart filtering + URL shortening + Duplicate detection")
    
    try:
        # Start both tasks concurrently
        await asyncio.gather(
            periodic_poster(),
            handle_admin_commands()
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
