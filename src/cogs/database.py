import pandas as pd

class DataBaseCog:
    def __init__(self):
        # file paths can be replaced with your actual file paths
        self.inventory_file_path = './src/cogs/inventory.parquet'
        self.chao_stats_file_path = './src/cogs/chao_stats.parquet'
        self.rings_file_path = './src/cogs/rings.parquet'
        self.nicknames_file_path = './src/cogs/nicknames.parquet'
        self.chao_file_path = './src/cogs/chao.parquet'

    # Function for inventory
    def store_inventory(self, user_id, inventory_data):
        inventory_df = pd.read_parquet(self.inventory_file_path)
        inventory_df.loc[user_id] = inventory_data
        inventory_df.to_parquet(self.inventory_file_path)
        
    def retrieve_inventory(self, user_id):
        inventory_df = pd.read_parquet(self.inventory_file_path)
        return inventory_df.loc[user_id]

    # Function for chao stats
    def store_chao_stats(self, user_id, chao_stats_data):
        chao_stats_df = pd.read_parquet(self.chao_stats_file_path)
        chao_stats_df.loc[user_id] = chao_stats_data
        chao_stats_df.to_parquet(self.chao_stats_file_path)

    def retrieve_chao_stats(self, user_id):
        chao_stats_df = pd.read_parquet(self.chao_stats_file_path)
        return chao_stats_df.loc[user_id]

    # Function for rings
    def store_rings(self, user_id, rings_data):
        rings_df = pd.read_parquet(self.rings_file_path)
        rings_df.loc[user_id] = rings_data
        rings_df.to_parquet(self.rings_file_path)
    
    def retrieve_rings(self, user_id):
        rings_df = pd.read_parquet(self.rings_file_path)
        return rings_df.loc[user_id]

    # Function for nicknames
    def store_nicknames(self, user_id, nicknames_data):
        nicknames_df = pd.read_parquet(self.nicknames_file_path)
        nicknames_df.loc[user_id] = nicknames_data
        nicknames_df.to_parquet(self.nicknames_file_path)

    def retrieve_nicknames(self, user_id):
        nicknames_df = pd.read_parquet(self.nicknames_file_path)
        return nicknames_df.loc[user_id]

    # Function for chao information
    def store_chao_info(self, user_id, chao_info):
        chao_df = pd.read_parquet(self.chao_file_path)
        chao_df.loc[user_id] = chao_info
        chao_df.to_parquet(self.chao_file_path)

    def retrieve_chao_info(self, user_id):
        chao_df = pd.read_parquet(self.chao_file_path)
        return chao_df.loc[user_id]
