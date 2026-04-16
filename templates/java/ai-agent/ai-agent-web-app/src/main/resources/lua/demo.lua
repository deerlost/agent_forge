-- 在lua脚本中，有两个全局的变量，是用来接收redis应用端传递的键值和其它参数的，
-- 分别为KEYS、ARGV。
-- 在应用端传递给KEYS时是一个数组列表，在lua脚本中通过索引方式获取数组内的值。
-- 在应用端，传递给ARGV的参数比较灵活，可以是多个独立的参数，但对应到Lua脚本中是，
-- 统一用ARGV这个数组接收，获取方式也是通过数组下标获取。
-- tonumber 把字符串转成数值
local value_key = KEYS[1]
local value_avg = ARGV[1]

-- lua中定义函数（根据字符串分割一个数组）
local function tt_split(str , reps)
    local resultStrList = {}
    string.gsub(str, "[^"..reps.."]+", function(w) table.insert(resultStrList, w) end)
    return resultStrList
end

-- key如果不存在重新给他设置值，并添加失效时间
if tonumber(redis.call('EXISTS', value_key)) == 0 then
    redis.call('SET', value_key, '语文;数学;英语;化学')
    redis.call('EXPIRE', value_key, 60)
end
-- 获取value_key里面的内容
local values = redis.call('get', value_key)
-- 调用函数进行字符串分割
local value_list= tt_split(values,";")

for i = 1, #value_list do
    local value = '"'..value_list[i]..'"';
    if value == value_avg then
        return 11111
    end
end
return 22222
