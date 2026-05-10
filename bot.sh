echo -e "\n${CYAN}📜 Showing Live Logs (Press Ctrl+C to return to menu)...${NC}\n"
docker-compose logs -f trading-agent
;;

4)
    echo -e "\n${CYAN}🔍 Scanning All Stocks...${NC}\n"
    docker-compose exec trading-agent python main.py --scan
    read -p "Press Enter to return to menu..."
    ;;

5)
    read -p "Enter Ticker (e.g., RELIANCE.NS): " ticker
    echo -e "\n${CYAN}🏢 Checking Fundamentals for $ticker...${NC}\n"
    docker-compose exec trading-agent python main.py --health --ticker "$ticker"
    read -p "Press Enter to return to menu..."
    ;;

6)
    read -p "Enter Ticker (e.g., TCS.NS): " ticker
    echo -e "\n${CYAN}📡 Getting Signal for $ticker...${NC}\n"
    docker-compose exec trading-agent python main.py --signal --ticker "$ticker"
    read -p "Press Enter to return to menu..."
    ;;

7)
    echo -e "\n${CYAN}🧠 Forcing Model Retraining...${NC}\n"
    docker-compose exec trading-agent python main.py --train
    read -p "Press Enter to return to menu..."
    ;;

8)
    echo -e "\n${CYAN}📊 Running Backtest...${NC}\n"
    docker-compose exec trading-agent python main.py --backtest
    read -p "Press Enter to return to menu..."
    ;;

9)
    echo -e "\n${GREEN}🌐 Open these links in your browser:${NC}"
    echo -e "   📈 Grafana (Dashboards): ${CYAN}http://localhost:3000${NC} (admin/admin123)"
    echo -e "   📊 Prometheus (Metrics): ${CYAN}http://localhost:9090${NC}"
    read -p "Press Enter to return to menu..."
    ;;

0)
    echo -e "\n${GREEN}👋 Exiting Control Panel. Bot will keep running in background!${NC}\n"
    exit 0
    ;;

*)
    echo -e "\n${RED}❌ Invalid option. Please select 0-9.${NC}"
    sleep 1
    ;;
