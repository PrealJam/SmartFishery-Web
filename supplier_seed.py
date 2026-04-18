"""
供应商管理数据初始化补充模块
"""

from datetime import datetime, timedelta
import random


def register_supplier_seed_functions(db, Supplier, SeedlingProduct, SeedlingInventory, PurchaseOrder, OrderItem, User, Pond):
    """注册供应商相关的种子数据函数"""
    
    def add_suppliers():
        """添加测试供应商"""
        print("\n正在添加供应商数据...")
        
        suppliers_data = [
            {
                'name': '清源水产养殖基地',
                'contact_person': '王经理',
                'phone': '13800138001',
                'email': 'supplier1@fishery.com',
                'address': '浙江省杭州市西湖区',
                'registration_date': datetime.utcnow().date(),
                'status': 'active',
                'notes': '专业草鱼苗供应商'
            },
            {
                'name': '锦鲤养殖中心',
                'contact_person': '李总',
                'phone': '13800138002',
                'email': 'supplier2@fishery.com',
                'address': '江苏省无锡市滨湖区',
                'registration_date': datetime.utcnow().date(),
                'status': 'active',
                'notes': '优质鲈鱼鱼苗供应'
            },
            {
                'name': '生态鱼苗繁育场',
                'contact_person': '陈女士',
                'phone': '13800138003',
                'email': 'supplier3@fishery.com',
                'address': '江西省南昌市青云谱区',
                'registration_date': datetime.utcnow().date(),
                'status': 'active',
                'notes': '鲤鱼、鲶鱼苗种'
            }
        ]
        
        try:
            suppliers = []
            for data in suppliers_data:
                supplier = Supplier(**data)
                db.session.add(supplier)
                suppliers.append(supplier)
            
            db.session.commit()
            suppliers = Supplier.query.all()
            print(f"✓ 成功添加 {len(suppliers)} 个供应商")
            return suppliers
        except Exception as e:
            print(f"✗ 添加供应商失败: {e}")
            db.session.rollback()
            return []

    
    def add_seedling_products(suppliers):
        """添加鱼苗产品"""
        print("\n正在添加鱼苗产品...")
        
        products_template = [
            {
                'supplier_idx': 0,  # 清源 - 草鱼苗
                'product_name': '一龄草鱼苗',
                'species': '草鱼',
                'grade': '一龄优质',
                'unit_price': 0.8,
                'cost_price': 0.4,
                'growth_cycle_days': 180,
                'survival_rate': 95.0,
                'description': '健壮活力强，存活率高'
            },
            {
                'supplier_idx': 0,
                'product_name': '二龄草鱼苗',
                'species': '草鱼',
                'grade': '二龄',
                'unit_price': 1.5,
                'cost_price': 0.7,
                'growth_cycle_days': 120,
                'survival_rate': 98.0,
                'description': '大规格草鱼苗'
            },
            {
                'supplier_idx': 1,  # 锦鲤 - 鲈鱼苗
                'product_name': '鲈鱼苗（寸苗）',
                'species': '鲈鱼',
                'grade': '寸苗',
                'unit_price': 2.0,
                'cost_price': 1.0,
                'growth_cycle_days': 150,
                'survival_rate': 92.0,
                'description': '优质鲈鱼种苗'
            },
            {
                'supplier_idx': 1,
                'product_name': '鲈鱼苗（尾苗）',
                'species': '鲈鱼',
                'grade': '尾苗',
                'unit_price': 1.2,
                'cost_price': 0.6,
                'growth_cycle_days': 180,
                'survival_rate': 90.0,
                'description': '经济实惠的鲈鱼苗'
            },
            {
                'supplier_idx': 2,  # 生态 - 混合
                'product_name': '鲤鱼苗',
                'species': '鲤鱼',
                'grade': '一龄',
                'unit_price': 0.6,
                'cost_price': 0.3,
                'growth_cycle_days': 200,
                'survival_rate': 93.0,
                'description': '健壮的鲤鱼苗'
            },
            {
                'supplier_idx': 2,
                'product_name': '鲶鱼苗',
                'species': '鲶鱼',
                'grade': '寸苗',
                'unit_price': 1.8,
                'cost_price': 0.9,
                'growth_cycle_days': 160,
                'survival_rate': 94.0,
                'description': '生长快的鲶鱼苗'
            }
        ]
        
        try:
            products = []
            for template in products_template:
                idx = template.pop('supplier_idx')
                if idx < len(suppliers):
                    product = SeedlingProduct(
                        supplier_id=suppliers[idx].id,
                        **template
                    )
                    db.session.add(product)
                    products.append(product)
            
            db.session.commit()
            products = SeedlingProduct.query.all()
            print(f"✓ 成功添加 {len(products)} 个鱼苗产品")
            return products
        except Exception as e:
            print(f"✗ 添加产品失败: {e}")
            db.session.rollback()
            return []

    
    def add_seedling_inventory(suppliers, products):
        """初始化库存"""
        print("\n正在初始化库存...")
        
        try:
            inventory_count = 0
            for product in products:
                inventory = SeedlingInventory(
                    supplier_id=product.supplier_id,
                    product_id=product.id,
                    quantity=random.randint(1000, 5000),
                    updated_by='system'
                )
                db.session.add(inventory)
                inventory_count += 1
            
            db.session.commit()
            print(f"✓ 成功初始化 {inventory_count} 条库存记录")
        except Exception as e:
            print(f"✗ 库存初始化失败: {e}")
            db.session.rollback()

    
    def add_supplier_users():
        """添加供应商用户"""
        print("\n正在添加供应商用户...")
        
        suppliers = Supplier.query.all()
        
        users_data = [
            {
                'username': 'supplier1',
                'password_hash': 'supplier123',
                'role': 'supplier',
                'supplier_id': suppliers[0].id if len(suppliers) > 0 else None,
                'email': 'user1@supplier1.com',
                'full_name': '张供应商'
            },
            {
                'username': 'supplier2',
                'password_hash': 'supplier123',
                'role': 'supplier',
                'supplier_id': suppliers[1].id if len(suppliers) > 1 else None,
                'email': 'user2@supplier2.com',
                'full_name': '李供应商'
            }
        ]
        
        try:
            added_count = 0
            for user_data in users_data:
                # 仅添加有效的供应商用户
                if user_data['supplier_id']:
                    if not User.query.filter_by(username=user_data['username']).first():
                        user = User(**user_data)
                        db.session.add(user)
                        added_count += 1
            
            db.session.commit()
            print(f"✓ 成功添加 {added_count} 个供应商用户")
        except Exception as e:
            print(f"✗ 添加供应商用户失败: {e}")
            db.session.rollback()

    
    def add_sample_purchase_orders(suppliers, products):
        """添加示例采购订单"""
        print("\n正在添加采购订单...")
        
        if not suppliers or not products:
            print("✗ 缺少供应商或产品数据，跳过订单创建")
            return
        
        ponds = Pond.query.all()
        if not ponds:
            print("✗ 缺少鱼池数据，跳过订单创建")
            return
        
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            print("✗ 缺少管理员用户，跳过订单创建")
            return
        
        try:
            order_count = 0
            statuses = ['draft', 'confirmed', 'shipped', 'received']
            
            for i in range(10):  # 创建10个订单
                supplier = random.choice(suppliers)
                pond = random.choice(ponds)
                
                order = PurchaseOrder(
                    supplier_id=supplier.id,
                    pond_id=pond.id,
                    created_by=admin_user.id,
                    expected_delivery_date=datetime.utcnow().date() + timedelta(days=random.randint(1, 7)),
                    status=random.choice(statuses),
                    notes=f'采购订单 #{i+1}'
                )
                
                # 添加2-4个订单项
                total_amount = 0
                supplier_products = [p for p in products if p.supplier_id == supplier.id]
                if supplier_products:
                    for j in range(random.randint(2, 4)):
                        product = random.choice(supplier_products)
                        quantity = random.randint(100, 1000)
                        unit_price = product.unit_price
                        
                        item = OrderItem(
                            product_id=product.id,
                            quantity=quantity,
                            unit_price=unit_price
                        )
                        order.items.append(item)
                        total_amount += quantity * unit_price
                
                order.total_amount = total_amount
                db.session.add(order)
                order_count += 1
            
            db.session.commit()
            print(f"✓ 成功添加 {order_count} 个采购订单")
        except Exception as e:
            print(f"✗ 添加订单失败: {e}")
            db.session.rollback()
    
    
    return {
        'add_suppliers': add_suppliers,
        'add_seedling_products': add_seedling_products,
        'add_seedling_inventory': add_seedling_inventory,
        'add_supplier_users': add_supplier_users,
        'add_sample_purchase_orders': add_sample_purchase_orders
    }
