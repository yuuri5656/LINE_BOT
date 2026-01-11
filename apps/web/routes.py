from flask import Blueprint, render_template, jsonify, request
import os

liff_blueprint = Blueprint('liff', __name__, template_folder='../../static/liff', static_folder='../../static')

@liff_blueprint.route('/liff/index')
def index():
    return render_template('index.html', liff_id=os.environ.get('LIFF_ID', ''))

@liff_blueprint.route('/liff/gacha')
def gacha():
    return render_template('gacha.html', liff_id=os.environ.get('LIFF_ID', ''))

@liff_blueprint.route('/liff/inventory')
def inventory():
    return render_template('inventory.html', liff_id=os.environ.get('LIFF_ID', ''))

@liff_blueprint.route('/liff/trade')
def trade():
    return render_template('trade.html', liff_id=os.environ.get('LIFF_ID', ''))

# API Endpoints

@liff_blueprint.route('/api/gacha/list')
def gacha_list():
    from apps.gacha.gacha_service import gacha_service
    return jsonify(gacha_service.get_gacha_list())

@liff_blueprint.route('/api/gacha/draw', methods=['POST'])
def gacha_draw():
    data = request.json
    user_id = data.get('userId')
    gacha_id = data.get('gachaId')
    count = data.get('count', 1)
    
    if not user_id or not gacha_id:
        return jsonify({'success': False, 'message': 'Invalid parameters'})
        
    from apps.gacha.gacha_service import gacha_service
    success, msg, items = gacha_service.draw_gacha(user_id, gacha_id, count)
    return jsonify({'success': success, 'message': msg, 'items': items})

@liff_blueprint.route('/api/inventory/list')
def inventory_list():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify([])
    
    from apps.inventory.inventory_service import inventory_service
    return jsonify(inventory_service.get_inventory(user_id))

@liff_blueprint.route('/api/inventory/equip', methods=['POST'])
def inventory_equip():
    data = request.json
    user_id = data.get('userId')
    slot = data.get('slot')
    card_id = data.get('cardId')
    
    from apps.inventory.inventory_service import inventory_service
    success, msg = inventory_service.equip_item(user_id, slot, card_id)
    return jsonify({'success': success, 'message': msg})

@liff_blueprint.route('/api/trade/create', methods=['POST'])
def trade_create():
    data = request.json
    sender_id = data.get('senderId')
    receiver_id = data.get('receiverId') # LINE User ID (Provider's ID, need to map?)
    # Note: receiver_id typically comes from user input or selection. 
    # For now, let's assume raw user_id or strict mapping is needed.
    
    offered = data.get('offered', [])
    requested = data.get('requested', [])
    
    from apps.trade.trade_service import trade_service
    success, msg, trade_id = trade_service.create_trade(sender_id, receiver_id, offered, requested)
    return jsonify({'success': success, 'message': msg, 'tradeId': trade_id})

@liff_blueprint.route('/api/trade/accept', methods=['POST'])
def trade_accept():
    data = request.json
    user_id = data.get('userId')
    trade_id = data.get('tradeId')
    
    from apps.trade.trade_service import trade_service
    success, msg = trade_service.accept_trade(trade_id, user_id)
    return jsonify({'success': success, 'message': msg})

