SELECT 
    reference_period, 
    value, 
    display_value, 
    retrieved_at 
FROM indicators 
WHERE indicator_name = '10-Year Treasury Yield'
ORDER BY reference_period ASC;
