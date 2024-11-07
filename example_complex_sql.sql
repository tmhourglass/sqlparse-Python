-- 示例1：复杂子查询和JOIN
WITH user_orders AS (
    SELECT
        u.user_id,
        u.username,
        COUNT(o.order_id) as order_count,
        SUM(o.total_amount) as total_spent
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    WHERE u.status = 'active'
    GROUP BY u.user_id, u.username
)
INSERT INTO user_statistics (user_id, username, order_metrics, avg_order_value)
SELECT
    uo.user_id,
    uo.username,
    uo.order_count,
    CASE
        WHEN uo.order_count > 0 THEN uo.total_spent / uo.order_count
        ELSE 0
    END as avg_order_value
FROM user_orders uo
WHERE uo.total_spent > 1000;

-- 示例2：多表联合统计
CREATE TABLE monthly_product_analysis AS
SELECT
    p.category_id,
    c.category_name,
    DATE_TRUNC('month', o.order_date) as sale_month,
    COUNT(DISTINCT o.order_id) as total_orders,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.quantity * p.unit_price) as total_revenue,
    AVG(r.rating) as avg_rating
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN product_reviews r ON p.product_id = r.product_id
WHERE o.order_date >= DATEADD(month, -12, GETDATE())
GROUP BY p.category_id, c.category_name, DATE_TRUNC('month', o.order_date)
HAVING COUNT(DISTINCT o.order_id) > 10;

-- 示例3：复杂更新语句
UPDATE customer_segments cs
SET
    segment_name = CASE
        WHEN avg_purchase > 1000 THEN 'Premium'
        WHEN avg_purchase > 500 THEN 'Gold'
        ELSE 'Regular'
    END,
    last_updated = CURRENT_TIMESTAMP
FROM (
    SELECT
        c.customer_id,
        AVG(o.total_amount) as avg_purchase,
        COUNT(o.order_id) as order_count,
        SUM(CASE WHEN p.category_id = 1 THEN oi.quantity ELSE 0 END) as category_1_purchases
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_date >= DATEADD(year, -1, GETDATE())
    GROUP BY c.customer_id
) purchase_stats
WHERE cs.customer_id = purchase_stats.customer_id
AND (purchase_stats.order_count >= 5 OR purchase_stats.category_1_purchases > 10);

-- 示例4：复杂分析查询
WITH daily_sales AS (
    SELECT
        DATE_TRUNC('day', o.order_date) as sale_date,
        p.supplier_id,
        s.supplier_name,
        p.category_id,
        SUM(oi.quantity * p.unit_price) as daily_revenue,
        COUNT(DISTINCT o.order_id) as order_count
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN suppliers s ON p.supplier_id = s.supplier_id
    WHERE o.order_date >= DATEADD(month, -3, GETDATE())
    GROUP BY DATE_TRUNC('day', o.order_date), p.supplier_id, s.supplier_name, p.category_id
),
supplier_rankings AS (
    SELECT
        supplier_id,
        supplier_name,
        SUM(daily_revenue) as total_revenue,
        AVG(daily_revenue) as avg_daily_revenue,
        ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY SUM(daily_revenue) DESC) as rank_in_category
    FROM daily_sales
    GROUP BY supplier_id, supplier_name, category_id
)
SELECT
    sr.supplier_name,
    c.category_name,
    sr.total_revenue,
    sr.avg_daily_revenue,
    sr.rank_in_category,
    CASE
        WHEN sr.rank_in_category = 1 THEN 'Category Leader'
        WHEN sr.rank_in_category <= 3 THEN 'Top Performer'
        ELSE 'Standard'
    END as performance_tier
FROM supplier_rankings sr
JOIN categories c ON sr.category_id = c.category_id
WHERE sr.rank_in_category <= 5
ORDER BY c.category_name, sr.rank_in_category;

-- 血缘关系说明：
/*
示例1血缘关系：
表：users -> orders -> user_statistics
字段：
- users(user_id, username, status)
- orders(order_id, user_id, total_amount)
- user_statistics(user_id, username, order_metrics, avg_order_value)

示例2血缘关系：
表：products -> categories -> order_items -> orders -> product_reviews -> monthly_product_analysis
字段：
- products(product_id, category_id, unit_price)
- categories(category_id, category_name)
- order_items(order_id, product_id, quantity)
- orders(order_id, order_date)
- product_reviews(product_id, rating)
- monthly_product_analysis(所有计算字段)

示例3血缘关系：
表：customers -> orders -> order_items -> products -> customer_segments
字段：
- customers(customer_id)
- orders(order_id, customer_id, total_amount, order_date)
- order_items(order_id, product_id, quantity)
- products(product_id, category_id)
- customer_segments(customer_id, segment_name, last_updated)

示例4血缘关系：
表：orders -> order_items -> products -> suppliers -> categories
字段：
- orders(order_id, order_date)
- order_items(order_id, product_id, quantity)
- products(product_id, supplier_id, category_id, unit_price)
- suppliers(supplier_id, supplier_name)
- categories(category_id, category_name)
*/


-- 这个文件包含了四个复杂SQL示例，每个示例都附带了详细的血缘关系说明。这些SQL可以用来测试血缘分析工具的各种功能，包括：
-- 1. 表关系追踪
-- 2. 字段依赖分析
-- 3. 复杂表达式处理
-- 4. 临时表血缘关系

