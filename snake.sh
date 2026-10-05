#!/bin/bash
# 貪吃蛇 (Snake) - 相容 macOS 內建 bash 3.2
# 操作: 方向鍵 或 W/A/S/D 移動, q 離開

W=30
H=20
GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
NC=$'\033[0m'

old_stty=$(stty -g)

cleanup() {
	stty "$old_stty"
	printf '\033[?25h\033[?1049l'
}
trap cleanup EXIT
trap 'exit 0' INT TERM

# 每 0.1 秒讀不到按鍵就繼續 (bash 3.2 的 read -t 不支援小數)
stty -echo -icanon min 0 time 1
printf '\033[?1049h\033[?25l'

place_food() {
	local ok i
	while :; do
		fx=$((RANDOM % W))
		fy=$((RANDOM % H))
		ok=1
		for ((i = 0; i < ${#xs[@]}; i++)); do
			if [ "${xs[i]}" -eq "$fx" ] && [ "${ys[i]}" -eq "$fy" ]; then
				ok=0
				break
			fi
		done
		[ $ok -eq 1 ] && return
	done
}

draw() {
	local x y i line border=""
	local cells=()
	for ((i = 0; i < W * H; i++)); do cells[i]="  "; done
	cells[fy * W + fx]="${RED}● ${NC}"
	for ((i = ${#xs[@]} - 1; i >= 0; i--)); do
		if [ $i -eq 0 ]; then
			cells[ys[i] * W + xs[i]]="${GREEN}██${NC}"
		else
			cells[ys[i] * W + xs[i]]="${GREEN}▓▓${NC}"
		fi
	done
	for ((x = 0; x < W; x++)); do border="$border──"; done

	local out=$'\033[H'
	out="$out分數: $score   (方向鍵/WASD 移動, q 離開)"$'\033[K\n'
	out="$out┌${border}┐"$'\n'
	for ((y = 0; y < H; y++)); do
		line=""
		for ((x = 0; x < W; x++)); do line="$line${cells[y * W + x]}"; done
		out="$out│${line}│"$'\n'
	done
	out="$out└${border}┘"$'\n'
	printf '%s' "$out"
}

xs=(15 14 13)
ys=(10 10 10)
dx=1
dy=0
score=0
place_food
printf '\033[2J'

while :; do
	draw

	key=""
	IFS= read -rsn1 key
	if [ "$key" = $'\033' ]; then
		IFS= read -rsn2 rest
		key="$rest"
	fi
	case "$key" in
		'[A' | w | W) [ $dy -ne 1 ] && { dx=0; dy=-1; } ;;
		'[B' | s | S) [ $dy -ne -1 ] && { dx=0; dy=1; } ;;
		'[C' | d | D) [ $dx -ne -1 ] && { dx=1; dy=0; } ;;
		'[D' | a | A) [ $dx -ne 1 ] && { dx=-1; dy=0; } ;;
		q | Q) exit 0 ;;
	esac

	nx=$((xs[0] + dx))
	ny=$((ys[0] + dy))

	dead=0
	if [ $nx -lt 0 ] || [ $nx -ge $W ] || [ $ny -lt 0 ] || [ $ny -ge $H ]; then
		dead=1
	else
		for ((i = 0; i < ${#xs[@]} - 1; i++)); do
			if [ "${xs[i]}" -eq $nx ] && [ "${ys[i]}" -eq $ny ]; then
				dead=1
				break
			fi
		done
	fi

	if [ $dead -eq 1 ]; then
		printf '\033[%d;1H' $((H + 4))
		printf 'GAME OVER! 最終分數: %d\n按任意鍵離開...' "$score"
		stty -echo -icanon min 1 time 0
		IFS= read -rsn1 _
		exit 0
	fi

	xs=("$nx" "${xs[@]}")
	ys=("$ny" "${ys[@]}")
	if [ $nx -eq $fx ] && [ $ny -eq $fy ]; then
		score=$((score + 10))
		place_food
	else
		last=$((${#xs[@]} - 1))
		xs=("${xs[@]:0:$last}")
		ys=("${ys[@]:0:$last}")
	fi
done
